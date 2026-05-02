from cryptabank import app
from functools import wraps
from flask import render_template, make_response, request, redirect, url_for, jsonify, g
from cryptabank.core.utils import Utils
from cryptabank.models import Model, init_db
import requests
from sqlite3 import IntegrityError

database = Model()
init_db()
app.url_map.strict_slashes = False


# ──────────────────────────────────────────────
# HELPERS DE AUTH
# ──────────────────────────────────────────────

def isauth(cookie):
    return database.is_auth(cookie)

def get_admin_nivel(cookie):
    """Retorna 0 (suporte), 1 (admin) ou None (nao autorizado)."""
    return database.get_admin_nivel(cookie)

def admin_required(func):
    """Qualquer nivel de admin pode acessar (0 = suporte, 1 = admin)."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        cookie = request.cookies.get('admin_token')
        nivel = get_admin_nivel(cookie)
        if nivel is None:
            return redirect(url_for('admin_login'))
        g.admin_nivel = nivel
        return func(*args, **kwargs)
    return wrapper

def admin_full_required(func):
    """Apenas admins de nivel 1 (admin completo) podem acessar."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        cookie = request.cookies.get('admin_token')
        nivel = get_admin_nivel(cookie)
        if nivel is None:
            return redirect(url_for('admin_login'))
        if nivel < 1:
            return render_template('admin/acesso_negado.html', admin_nivel=nivel), 403
        g.admin_nivel = nivel
        return func(*args, **kwargs)
    return wrapper


def _admin_nivel():
    """Helper para pegar nivel do admin logado na request atual."""
    cookie = request.cookies.get('admin_token')
    return get_admin_nivel(cookie)


# ──────────────────────────────────────────────
# LANDING PAGE
# ──────────────────────────────────────────────

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


# ──────────────────────────────────────────────
# AUTENTICACAO
# ──────────────────────────────────────────────

@app.route('/login')
def login():
    erro = request.args.get('erro', '')
    if isauth(request.cookies.get('auth_token')):
        return redirect(url_for('painel'))
    return render_template('auth/login.html', endpoint='verifica_login', erro=erro)


@app.route('/verifica_login', methods=['POST'])
def verifica_login():
    infos = request.form.to_dict()

    # Verifica se conta existe e nao esta bloqueada
    if not database.login(infos):
        # Verifica se o motivo e bloqueio
        if database.is_bloqueado(infos.get('email', '')):
            return redirect(url_for('login', erro='Conta bloqueada. Entre em contato com o suporte.'))
        return redirect(url_for('login', erro='Email ou senha incorretos.'))

    cookie_value = database.get_cookie(infos['email'])
    response = make_response(redirect(url_for('painel')))
    response.set_cookie('auth_token', cookie_value)
    return response


@app.route('/cadastro')
def cadastro():
    erro = request.args.get('erro', '')
    if isauth(request.cookies.get('auth_token')):
        return redirect(url_for('homepage'))
    return render_template('auth/cadastro.html', erro=erro)


@app.route('/cadastrar_user', methods=['POST'])
def verifica_cad():
    infos = request.form.to_dict()

    if infos.get('confirmar_senha') != infos.get('senha'):
        return redirect(url_for('cadastro', erro='As senhas nao coincidem.'))

    try:
        auth = database.cadastrar(infos)
    except IntegrityError:
        return redirect(url_for('cadastro', erro='Erro no Cadastro: email ja existe.'))

    if not auth:
        return redirect(url_for('cadastro', erro='Erro no Cadastro. Verifique as informacoes.'))

    cookie_value = Utils.uuid(True)
    database.save_cookie(cookie_value, infos['email'])
    return redirect(url_for('login'))


@app.route('/logout')
def logout():
    response = make_response(redirect(url_for('homepage')))
    response.set_cookie('auth_token', '', max_age=0)
    return response


# ──────────────────────────────────────────────
# PAINEL DE USUARIO
# ──────────────────────────────────────────────

@app.route('/painel')
def painel():
    aviso = request.args.get('aviso')
    erro  = request.args.get('error', 'ok')

    token = request.cookies.get('auth_token')
    if not isauth(token):
        return redirect(url_for('login'))

    user_infos = database.get_user_infos(token)
    if not user_infos:
        return redirect(url_for('logout'))

    transacoes = database.get_transactions_history(user_infos['conta_id'])

    try:
        currency = requests.post('http://127.0.0.1:9999/api/get-currency', json=user_infos, timeout=3).json()
        saldo = float(currency.get('currency', 0)) / 100
    except Exception:
        saldo = 0.0

    try:
        warnings = requests.get('http://127.0.0.1:9999/api/warnings',
                                params={'conta_id': user_infos['conta_id']}, timeout=3).json()
    except Exception:
        warnings = []

    return render_template(
        'painel_user/painel_usuario.html',
        saldo=saldo,
        nome=user_infos['nome'],
        aviso=aviso,
        erro=erro,
        warning=warnings,
        transacoes=transacoes
    )


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
    token = request.cookies.get('auth_token')
    if not isauth(token):
        return redirect(url_for('login'))
    chamados = database.get_chamados_by_token(token)
    return render_template('painel_user/suporte.html', aviso=aviso, chamados=chamados)


@app.route('/painel/contatar-suporte/enviar', methods=['POST'])
def enviar_suporte():
    mensagem = request.form.to_dict()
    token = request.cookies.get('auth_token')
    if not isauth(token):
        return redirect(url_for('login'))
    database.registrar_mensagem(mensagem, token)
    return redirect(url_for('contatar_suporte', aviso='Solicitação enviada! Nossa equipe responderá em breve.', aba='meus'))


@app.route('/painel/transferencia')
def detalhe_transf():
    token = request.cookies.get('auth_token')
    if not isauth(token):
        return redirect(url_for('login'))

    transf_id = request.args.get('id')
    transacao = database.get_transaction_by_id(transf_id)
    if not transacao:
        return redirect(url_for('painel'))

    nome_destino = database.get_user_name_by_transfKey(transacao['destiny_wallet'])
    return render_template('painel_user/transf-detalhada.html',
                           t=transacao, nome=nome_destino['nome'])


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
    dados = request.form.to_dict()
    dados.update(user_infos)

    try:
        currency = requests.post('http://127.0.0.1:9999/api/get-currency',
                                 json=user_infos, timeout=3).json().get('currency', 0)
    except Exception:
        return redirect(url_for('painel', aviso='Servico indisponivel.', error='erro'))

    valor_cents = int(float(dados.get('valor', 0)) * 100)

    if valor_cents <= 0:
        return redirect(url_for('painel', aviso='Valor invalido!', error='erro'))
    if int(currency) < valor_cents:
        return redirect(url_for('painel', aviso='Saldo insuficiente!', error='erro'))

    dados['valor'] = str(valor_cents)
    dados['transaction_status'] = 'pending'
    dados['currency'] = currency

    try:
        requests.post('http://127.0.0.1:9999/api/request-transaction', json=dados, timeout=3)
    except Exception:
        return redirect(url_for('painel', aviso='Erro ao processar transferencia.', error='erro'))

    database.save_transfer(dados)
    return redirect(url_for('painel', aviso='Transferencia enviada para analise com sucesso!'))


# ──────────────────────────────────────────────
# PAINEL ADMIN — AUTH
# ──────────────────────────────────────────────

@app.route('/admin/login')
def admin_login():
    error = request.args.get('error')
    return render_template('admin/login.html', error=error)

@app.route('/admin/do-login', methods=['POST'])
def admin_dologin():
    infos = request.form.to_dict()
    if database.admin_login(infos):
        cookie_value = database.get_admin_cookie(infos['email'])
        if not cookie_value:
            # Gera cookie novo se nao existir
            cookie_value = Utils.uuid()
            database.save_admin_cookie(cookie_value, infos['email'])

        response = make_response(redirect(url_for('admin')))
        response.set_cookie('admin_token', cookie_value)
        return response

    return redirect(url_for('admin_login', error='Email ou senha incorretos.'))

@app.route('/admin/logout')
def admin_logout():
    response = make_response(redirect(url_for('admin_login')))
    response.set_cookie('admin_token', '', max_age=0)
    return response


# ──────────────────────────────────────────────
# PAINEL ADMIN — ROTAS (nivel 1 = admin pleno)
# ──────────────────────────────────────────────

@app.route('/admin')
@admin_required
def a():
    return redirect(url_for('admin'))

@app.route('/admin/home')
@admin_required
def admin():
    nivel = _admin_nivel()
    # Suporte (nivel=0) so pode acessar o painel de suporte
    if nivel == 0:
        return redirect(url_for('suporte'))

    infos = database.get_dashboard_infos()
    users = database.get_all_users()
    num_chamados = database.num_chamados()

    return render_template('admin/admin.html',
                           infos=infos, users=users,
                           num_chamados=num_chamados,
                           admin_nivel=nivel)

@app.route('/admin/conta', methods=['GET'])
@admin_full_required
def detailed_account():
    nivel = _admin_nivel()
    id_conta = request.args.get('id')
    usuario = database.get_user_info_by_id(id_conta)
    if not usuario:
        return redirect(url_for('admin'))

    data = {'conta_id': usuario['id'], 'email': usuario['email']}
    try:
        currency = requests.post('http://localhost:9999/api/get-currency',
                                 json=data, timeout=3).json().get('currency', 0)
        usuario['saldo'] = float(currency) / 100
    except Exception:
        usuario['saldo'] = 0.0

    return render_template('admin/info_user.html', usuario=usuario, admin_nivel=nivel)

@app.route('/admin/bloquear', methods=['GET'])
@admin_full_required
def bloquear_conta():
    account_id = request.args.get('id')
    if not account_id:
        return redirect(url_for('admin'))
    database.bloquear_conta(account_id)
    return redirect(url_for('detailed_account', id=account_id))

@app.route('/admin/desbloquear', methods=['GET'])
@admin_full_required
def desbloquear_conta():
    account_id = request.args.get('id')
    if not account_id:
        return redirect(url_for('admin'))
    database.desbloquear_conta(account_id)
    return redirect(url_for('detailed_account', id=account_id))

@app.route('/admin/transferencias')
@admin_full_required
def admin_transf():
    nivel = _admin_nivel()
    transfs = database.get_all_transfs()
    for t in transfs:
        t['valor'] = int(t['valor'])
    return render_template('admin/admin_transferencias.html', transfs=transfs, admin_nivel=nivel)

@app.route('/admin/transferencia/detalhe')
@admin_full_required
def admin_transf_detalhe():
    nivel = _admin_nivel()
    id_transf = request.args.get('id')
    transf = database.get_transf_by_id(id_transf)
    if not transf:
        return redirect(url_for('admin_transf'))

    transf['valor'] = int(transf['valor'])

    remetente = database.get_user_name_by_transfKey(transf['source_wallet'])
    destinatario = database.get_user_name_by_transfKey(transf['destiny_wallet'])

    return render_template('admin/transferencia_detalhe.html',
                           transf=transf,
                           nome_remetente=remetente['nome'],
                           nome_destinatario=destinatario['nome'],
                           admin_nivel=nivel)

@app.route('/admin/config')
@admin_full_required
def admin_config():
    nivel = _admin_nivel()
    return render_template('admin/config.html', admin_nivel=nivel)


# ──────────────────────────────────────────────
# PAINEL ADMIN — CRIAR ADMIN (so admin nivel 1)
# ──────────────────────────────────────────────

@app.route('/admin/create', methods=['GET'])
@admin_full_required
def criar_admin():
    nivel = _admin_nivel()
    erro = request.args.get('erro', '')
    sucesso = request.args.get('sucesso', '')
    admins = database.get_all_admins()
    return render_template('admin/create_acc.html',
                           erro=erro, sucesso=sucesso,
                           admins=admins, admin_nivel=nivel)

@app.route('/admin/create', methods=['POST'])
@admin_full_required
def cria_adm():
    infos = request.form.to_dict()

    # Valida campos obrigatorios
    if not infos.get('email') or not infos.get('senha') or not infos.get('nome'):
        return redirect(url_for('criar_admin', erro='Preencha todos os campos obrigatorios.'))

    if infos.get('confirmar_senha') != infos.get('senha'):
        return redirect(url_for('criar_admin', erro='As senhas nao coincidem.'))

    # Mapeia nivel: 'admin'=1, 'suporte'=0
    nivel_str = infos.get('nivel', 'suporte')
    infos['nivel'] = 1 if nivel_str == 'admin' else 0

    try:
        ok = database.cadastrar_admin(infos)
    except IntegrityError:
        return redirect(url_for('criar_admin', erro='Email ja cadastrado.'))

    if not ok:
        return redirect(url_for('criar_admin', erro='Erro ao criar administrador.'))

    # Gera e salva cookie para o novo admin
    cookie = Utils.uuid()
    database.save_admin_cookie(cookie, infos['email'])

    return redirect(url_for('criar_admin', sucesso=f'Administrador {infos["email"]} criado com sucesso!'))


# ──────────────────────────────────────────────
# PAINEL DE SUPORTE (nivel 0 e 1)
# ──────────────────────────────────────────────

@app.route('/admin/suporte')
@admin_required
def suporte():
    nivel = _admin_nivel()
    chamados = database.get_all_chamados()
    return render_template('admin/painel.html', chamados=chamados, admin_nivel=nivel)

@app.route('/admin/suporte/detalhes', methods=['GET'])
@admin_required
def detalhes_chamado():
    nivel = _admin_nivel()
    id_chamado = request.args.get('id')
    chamado = database.get_chamado_by_id(id_chamado)
    if not chamado:
        return redirect(url_for('suporte'))
    return render_template('admin/detalhes_chamado.html', chamado=chamado, admin_nivel=nivel)

@app.route('/admin/suporte/responder', methods=['POST'])
@admin_required
def responder_chamado():
    id_chamado = request.form.get('id')
    status = request.form.get('status', 'aberto')
    resposta = request.form.get('resposta', '')
    database.atualizar_chamado(id_chamado, status, resposta)
    return redirect(url_for('detalhes_chamado', id=id_chamado))

# Dev helper
@app.route('/showsuport')
def showsup():
    return jsonify(database.show_all_suport_messages())
