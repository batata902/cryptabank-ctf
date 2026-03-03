const cryptabank = document.querySelector('.logo')

const cards = document.querySelectorAll('.card-beneficio')

const card_sec = document.querySelector('.card-beneficio.seguranca')

try {
    for (let card of cards) {
        card.addEventListener('mouseenter', function (e) {
            card.classList.add('mouse-over')
        })
        card.addEventListener('mouseleave', function (e) {
            card.classList.remove('mouse-over')
        })
    }
    card_sec.addEventListener('click', function () {
        window.location.href = '/seguranca';
    });

    cryptabank.addEventListener('click', function () {
        window.location.href = '/';
    })
} catch (e) {
    null
}