from cryptabank import app
from flask import render_template, make_response, request, redirect, url_for

auth_users = []

def isauth(cookie):
    return cookie in auth_users


@app.route('/')
def homepage():
    autenticado = isauth(request.cookies.get('auth_token'))

    return render_template('index.html', autenticado=autenticado)

@app.route('/emprestimos')
def emprestimos():
    autenticado = isauth(request.cookies.get('auth_token'))

    return render_template('emprestimos.html', autenticado=autenticado)

@app.route('/login')
def login():
    if isauth(request.cookies.get('auth_token')):
            return redirect('/dashboard')
    return render_template('login.html')


@app.route('/cadastro')
def cadastro():
    if isauth(request.cookies.get('auth_token')):
            return redirect(url_for('homepage'))
    return render_template('cadastro.html')


@app.route('/painel')
def painel():
    #if not isauth(request.cookies.get('auth_token')):
    #        return redirect(url_for('login'))
    return render_template('painel_usuario.html', saldo='0,00')

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


@app.route('/cookie')
def getcookie():
    response = make_response('Cookie obtido')
    response.set_cookie('auth_token', 'abc123')
    return response