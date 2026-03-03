from cryptabank import app
from flask import render_template, make_response, request, redirect, url_for
from cryptabank.core.utils import Utils
from cryptabank.models import Model

auth_users = []
database = Model()

def isauth(cookie):
    return database.is_auth(cookie)


@app.route('/')
def homepage():
    autenticado = isauth(request.cookies.get('auth_token'))

    return render_template('index.html', autenticado=autenticado)

@app.route('/seguranca')
def seguranca():
    autenticado = isauth(request.cookies.get('auth_token'))
    return render_template('seguranca.html', autenticado=autenticado)


@app.route('/emprestimos')
def emprestimos():
    autenticado = isauth(request.cookies.get('auth_token'))

    return render_template('emprestimos.html', autenticado=autenticado)

@app.route('/login')
def login():
    erro = request.args.get('erro')
    if not erro:
         erro = ''
    if isauth(request.cookies.get('auth_token')):
            return redirect(url_for('painel'))
    return render_template('login.html', endpoint='verifica_login', erro=erro)


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
    return render_template('cadastro.html', erro=erro)


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
    
@app.route('/painel')
def painel():
    token = request.cookies.get('auth_token')
    if not isauth(token):
            return redirect(url_for('login'))
    user_infos = database.get_user_infos(token)
    print(float(user_infos['currency']) / 100)
    return render_template('painel_usuario.html', saldo=user_infos['currency'], nome=user_infos['nome'])

@app.route('/painel/transferir')
def transferir():
    #if not isauth(request.cookies.get('auth_token')):
    #    return redirect(url_for('login'))
    return render_template('transferir.html')


@app.route('/painel/suporte')
def slogin():
    #if not isauth(request.cookies.get('auth_token')):
    #    return redirect(url_for('login'))
    return render_template('login.html', endpoint='/suporte-auth')

@app.route('/contatar-suporte')
def contatar_suporte():
    #if not isauth(request.cookies.get('auth_token')):
    #    return redirect(url_for('login'))
    return render_template('suporte.html')

# @app.route('/painel/')
# def extrato():
#     None

# @app.route('/painel/')
# def investimentos():
#     None

@app.route('/logout')
def logout():
    response = make_response(redirect(url_for('homepage')))
    response.set_cookie('auth_token', '', max_age=0)

    return response