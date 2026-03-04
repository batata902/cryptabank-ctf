from cryptabank import app
from flask import render_template, make_response, request, redirect, url_for
from cryptabank.core.utils import Utils
from cryptabank.models import Model

auth_users = []
database = Model()

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
    
    auth = database.cadastrar(infos)
    cookie_value = Utils.uuid(True)
    database.save_cookie(cookie_value, infos['email'])

    if not auth:
         return redirect(url_for('cadastro.html', erro='Erro no Cadastro, verifique as informações e tente novamente.'))
    
    return redirect(url_for('login'))
    
# FIM AUTENTICAÇÃO


# INICIO PAINEL DE USUARIO

@app.route('/painel')
def painel():
    token = request.cookies.get('auth_token')
    if not isauth(token):
            return redirect(url_for('login'))
    user_infos = database.get_user_infos(token)
    print(float(user_infos['currency']) / 100)
    return render_template('painel_user/painel_usuario.html', saldo=user_infos['currency'], nome=user_infos['nome'])


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
    dados_transferencia = request.form.to_dict()
    dados_transferencia.update(database.get_all_user_infos(token))
    return dados_transferencia
