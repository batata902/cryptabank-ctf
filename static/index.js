const cryptabank = document.querySelector('.logo')

const cards = document.querySelectorAll('.card-beneficio')

const card_sec = document.querySelector('.card-beneficio.seguranca')
const card_trans = document.querySelector('.card-beneficio.transferencia')
const card_digital = document.querySelector('.card-beneficio.digital')


for (let card of cards) {
    card.addEventListener('mouseenter', function (e) {
        if (card.classList.contains('clicavel')) {
            card.style.cursor = 'pointer';
        }
        card.classList.add('mouse-over')
    })
    card.addEventListener('mouseleave', function (e) {
        card.classList.remove('mouse-over')
    })
}

try {
    card_sec.addEventListener('click', function () {
        window.location.href = '/seguranca';
    });
} catch (err) {
    null;
}

try{
    card_trans.addEventListener('click', function () {
        window.location.href = '/pix-ted';
    });
} catch (err) {
    null;
}

try {
    card_digital.addEventListener('click', function () {
        window.location.href = '/digital';
    })
} catch (err){
    null;
}

try {
    cryptabank.addEventListener('click', function () {
        window.location.href = '/';
    });
} catch(err) {
    null;
}
