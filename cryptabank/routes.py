from cryptabank import app
from flask import render_template, make_response, request, redirect, url_for
from cryptabank.core.utils import Utils
from cryptabank.models import Model
import requests
from sqlite3 import IntegrityError

auth_users = []
database = Model()
app.url_map.strict_slashes = False

def isauth(cookie):
    return database.is_auth(cookie)

# LANDING PAGE

@app.route('/')
def homepage():
    autenticado = isauth(request.cookies.get('auth_token'))

    return render_template('landing/index.html', autenticado=autenticado)

@app.route('/seguranca')
def seguranca():
    autenticado = isauth(request.cookies.get('auth_token'))
    return render_template('landing/seguranca.html', autenticado=autenticado)

@app.route('/pix-ted')
def pix_ted():
    autenticado = isauth(request.cookies.get('auth_token'))
    return render_template('landing/transferências_inst.html', autenticado=autenticado)

@app.route('/digital')
def digital():
    autenticado = isauth(request.cookies.get('auth_token'))
    return render_template('landing/digital.html', autenticado=autenticado)

# FIM LANDING PAGE

# INICIO AUTENTICAÇÃO

@app.route('/login')
def login():
    erro = request.args.get('erro')
    if not erro:
         erro = ''
    if isauth(request.cookies.get('auth_token')):
            return redirect(url_for('painel'))
    return render_template('auth/login.html', endpoint='verifica_login', erro=erro)


@app.route('/verifica_login', methods=['POST'])
def verifica_login():
    infos = request.form.to_dict()

    auth = database.login(infos)
    
    if not auth:
         return redirect(url_for('login', erro='Email ou senha incorretos.'))
    
    cookie_value = database.get_cookie(infos['email'])

    response = make_response(redirect(url_for('painel')))
    response.set_cookie('auth_token', cookie_value) 
    return response


@app.route('/cadastro')
def cadastro():
    erro = request.args.get('erro')
    if erro == None:
         erro = ''
    if isauth(request.cookies.get('auth_token')):
            return redirect(url_for('homepage'))
    return render_template('auth/cadastro.html', erro=erro)


@app.route('/cadastrar_user', methods=['POST'])
def verifica_cad():
    infos = request.form.to_dict()

    if infos['confirmar_senha'] != infos['senha']:
        return redirect(url_for('cadastro', erro='Email já existe ou houve algum problema na criação da conta'))

    try:
        auth = database.cadastrar(infos)
    except IntegrityError:
        return redirect(url_for('cadastro', erro='Erro no Cadastro, email já existe.'))
    
    if not auth:
        return redirect(url_for('cadastro', erro='Erro no Cadastro, verifique as informações e tente novamente.'))

    cookie_value = Utils.uuid(True)
    database.save_cookie(cookie_value, infos['email'])
    print(f'\033[33mAUTH\033[m ', auth)
    
    return redirect(url_for('login'))
    
# FIM AUTENTICAÇÃO


# INICIO PAINEL DE USUARIO

@app.route('/painel')
def painel():
    aviso = request.args.get('aviso')
    erro = request.args.get('error')
    if not erro:
        erro = 'ok'

    token = request.cookies.get('auth_token')
    if not isauth(token):
            return redirect(url_for('login'))
    
    user_infos = database.get_user_infos(token)
    transacoes = database.get_transactions_history(user_infos['conta_id'])

    currency = requests.post('http://127.0.0.1:9999/api/get-currency', json=user_infos).json()
    warnings = requests.get('http://127.0.0.1:9999/api/warnings', params={'conta_id': user_infos['conta_id']}).json()

    for t in transacoes:
        if t['destiny_wallet'] == '':
            database.delete_transfer(t['id'])
            transacoes.remove(t)

    return render_template('painel_user/painel_usuario.html', saldo=float(currency['currency']) / 100, nome=user_infos['nome'], aviso=aviso, erro=erro, warning=warnings, transacoes=transacoes)


@app.route('/painel/user-infos')
def user_infos():
    token = request.cookies.get('auth_token')
    if not isauth(token):
        return redirect(url_for('login'))
    
    usuario = database.get_all_user_infos(token)
    return render_template('painel_user/informacoes_usuario.html', usuario=usuario)


@app.route('/painel/contatar-suporte', methods=['GET'])
def contatar_suporte():
    aviso = request.args.get('aviso')
    if not isauth(request.cookies.get('auth_token')):
        return redirect(url_for('login'))
    return render_template('painel_user/suporte.html', aviso=aviso)


@app.route('/painel/contatar-suporte/enviar', methods=['POST'])
def enviar_suporte():
    mensagem = request.form.to_dict()
    token = request.cookies.get('auth_token')
    if not isauth(token):
         return redirect(url_for('login'))
    database.registrar_mensagem(mensagem, token)
    return redirect(url_for('contatar_suporte', aviso='Reclamação enviada!'))


@app.route('/showsuport')
def showsup():
    return database.show_all_suport_messages()


@app.route('/logout')
def logout():
    response = make_response(redirect(url_for('homepage')))
    response.set_cookie('auth_token', '', max_age=0)

    return response

@app.route('/painel/transferencia')
def detalhe_transf():
    transf = request.args.get('id')

    transacao = database.get_transaction_by_id(transf)
    nome_destino = database.get_user_name_by_transfKey(transacao['destiny_wallet'])

    return render_template('painel_user/transf-detalhada.html', t=transacao, nome=nome_destino['nome'])

# FIM PAINEL DE USUARIO

# Transferência (Ainda no painel do usuário)

@app.route('/painel/transferir')
def transferir():
    token = request.cookies.get('auth_token')
    if not isauth(token):
        return redirect(url_for('login'))
    return render_template('painel_user/transferir.html')


@app.route('/painel/realiza-transferencia', methods=['POST'])
def transferencia():
    token = request.cookies.get('auth_token')
    if not isauth(token):
         return redirect(url_for('login'))
    user_infos = database.get_all_user_infos(token)
    dados_transferencia = request.form.to_dict()

    print(dados_transferencia)

    dados_transferencia.update(user_infos)
    currency = requests.post('http://127.0.0.1:9999/api/get-currency', json=user_infos).json()['currency']

    if int(currency) < float(dados_transferencia['valor']) * 100:
        return redirect(url_for('painel', aviso='Dinheiro insuficiente!', error='erro'))
    elif float(dados_transferencia['valor'])*100 <= 0:
        return redirect(url_for('painel', aviso='Valor inválido!', error='erro'))
    
    valor = int(float(dados_transferencia['valor']) * 100) 
    dados_transferencia['valor'] = str(valor)
    dados_transferencia['transaction_status'] = 'pending'
    dados_transferencia['currency'] = currency

    requests.post('http://127.0.0.1:9999/api/request-transaction', json=dados_transferencia)

    database.save_transfer(dados_transferencia)

    return redirect(url_for('painel', aviso='Transferência enviada para análise com sucesso'))


# PAINEL ADMIN

@app.route('/admin')
def a():
    return redirect(url_for('admin'))

@app.route('/admin/home')
def admin():
    infos = database.get_dashboard_infos()
    users = database.get_all_users()
    num_chamados = database.num_chamados()

    print(infos)
    return render_template('admin/admin.html', infos=infos, users=users, num_chamados=num_chamados)

@app.route('/admin/conta', methods=['GET'])
def detailed_account():
    id_conta = request.args.get('id')

    return 'Fazer'

@app.route('/admin/transferencias')
def admin_transf():
    transfs = database.get_all_transfs()

    for t in transfs:
        t['valor'] = int(t['valor'])

    return render_template('admin/admin_transferencias.html', transfs=transfs)

@app.route('/admin/config')
def admin_config():
    return render_template('admin/config.html')


@app.route('/admin/detalhes')
def admin_detalhes():
    return render_template('admin/transferencia_detalhe.html')

# PAINEL DE SUPORTE

@app.route('/admin/suporte')
def suporte():
    chamados = database.get_all_chamados()

    return render_template('admin/painel.html', chamados=chamados)

@app.route('/admin/suporte/detalhes', methods=['GET'])
def detalhes_chamado():
    id_chamado = request.args.get('id')
    chamado = database.get_chamado_by_id(id_chamado)

    return render_template('admin/detalhes_chamado.html', chamado=chamado)

# FIM PAINEL DE SUPORTE