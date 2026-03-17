from flask import Flask, request, jsonify
from models import Database
import requests

app = Flask(__name__)
database = Database()

admin_token = '123456'

@app.route('/api/registrar-user', methods=['POST'])
def registrar():
    infos = request.get_json()

    database.registrar(infos)
    return jsonify({'status': 'ok'})


@app.route('/api/request-transaction', methods=['POST'])
def request_transaction():
    infos = request.get_json()

    infos['id'] = database.save_transaction(infos) # Salva no db como transação pendente
    # infos -> 
    database.realize_transaction(infos['conta_id'], int(infos['valor']))
    requests.post('http://127.0.0.1:5050/submit', json=infos) # Envia para análise de integridade

    return jsonify({'status': 'ok'})


@app.route('/api/submit-result', methods=['POST'])
def submit_result():
    infos = request.get_json()

    if infos['transaction_status'] == 'approved':
        database.realize_transaction(infos['destino'], int(infos['valor']) * (-1))

    elif infos['transaction_status'] == 'denied':
        database.realize_transaction(infos['conta_id'], int(infos['valor']) * (-1))
        database.set_warning(infos['conta_id'], 'Valor extornado!', 'Seu saldo já foi atualizado!')

    database.change_transaction_status(infos)

    return jsonify({'status': 'ok'})


@app.route('/api/get-currency', methods=['POST'])
def getcurrency():
    infos = request.get_json()
    currency = database.get_currency_infos(infos)
    return jsonify(currency)


@app.route('/api/user-exists', methods=['GET'])
def user_exists():
    account_id = request.args.get('conta_id')
    existe = database.account_exists(account_id)
    return jsonify({'status': existe})

@app.route('/api/warnings', methods=['GET'])
def warnings():
    user_id = request.args.get('conta_id')

    warning = database.get_all_warnings(user_id)
    return warning

@app.route('/api/total-em-contas')
def total_em_contas():
    total = database.get_total_currrency()
    return jsonify(total)

# DEV


@app.route('/api/see-all-transactions', methods=['GET'])
def see_trans():
    token = request.args.get('token')
    if token != admin_token:
        return jsonify({'status': 'forbbiden'})
    trans = database.get_all_transactions()
    return jsonify(trans)


@app.route('/api/users', methods=['GET'])
def users():
    token = request.args.get('token')
    if token != admin_token:
        return jsonify({'status': 'forbbiden'})
    users = database.get_all_users()
    return jsonify(users)

@app.route('/liquidity', methods=['GET'])
def liquidity():
    token = request.args.get('token')
    if token != admin_token:
        return jsonify({'status': 'forbbiden'})
    return jsonify(database.see_liquidity())


@app.route('/setcur')
def setcur():
    valor = request.args.get('valor')
    email = request.args.get('email')
    if not valor or not email:
        return {'status': 'need valor and email args'}
    database.set_currency(valor, email)
    return {'status': 'ok'}


if __name__ == '__main__':
    app.run(port=9999, debug=True)