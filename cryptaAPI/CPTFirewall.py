from flask import Flask, request
import requests

app = Flask(__name__)


@app.route('/submit', methods=['POST'])
def analyzer():
    infos = request.get_json()

    if conta_existe(infos['destino']):
        infos['transaction_status'] = 'approved'
    else:
        infos['transaction_status'] = 'denied'

    enviar_resultado(infos)
    return {'status': 'ok'}


def enviar_resultado(resultado):
    requests.post('http://127.0.0.1:9999/api/submit-result', json=resultado)


def conta_existe(conta_id):
    existe = requests.get('http://127.0.0.1:9999/api/user-exists', params=conta_id).json()
    if existe['status'] == 'true':
        return True
    return False

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)
