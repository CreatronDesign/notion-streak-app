const API = "/data";

let lastState = localStorage.getItem("lastState") === "true";

function load() {
fetch(API)
.then(r => r.json())
.then(d => {

let percent = d.total ? Math.round((d.done/d.total)*100) : 0;

document.getElementById("streak").innerText = d.streak;
document.getElementById("progress-text").innerText = percent + "%";

const circle = document.querySelector(".progress");
const radius = 54;
const circumference = 2 * Math.PI * radius;
const offset = circumference - (percent/100)*circumference;

circle.style.strokeDasharray = circumference;
circle.style.strokeDashoffset = offset;

let emoji = document.getElementById("fire-emoji");
let gif = document.getElementById("fire-img");
let popup = document.getElementById("popup");
let quote = document.getElementById("quote");

emoji.style.display = "block";
gif.style.display = "none";
quote.innerText = "KEEP GOING!";

if (d.total > 0 && d.all_done) {

    emoji.style.display = "none";
    gif.style.display = "block";
    quote.innerText = "You're on fire 🔥";

    if (!lastState) {
        popup.classList.add("show");
        confetti({
  particleCount: 90,
  spread: 80,
  scalar: 1.2
});

        setTimeout(() => {
            popup.classList.remove("show");
        }, 2000);
    }

    lastState = true;

} else {
    lastState = false;
}

localStorage.setItem("lastState", lastState);

})
.catch(err => console.log(err));
}

setInterval(load, 4000);
load();