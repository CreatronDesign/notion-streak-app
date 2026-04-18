fetch("/realm-data")
.then(r=>r.json())
.then(d=>{

document.getElementById("month").innerText = d.month;

let grid = document.getElementById("grid");

d.grid.forEach((x,i)=>{

    let div = document.createElement("div");
    div.className = "tile " + x.state;
    div.innerText = x.in_month ? x.day : "";

    if(x.url){
        div.onclick = ()=> window.open(x.url,"_blank");
    }

    grid.appendChild(div);
});

let year = document.getElementById("year");

d.year.forEach(m=>{

    let box = document.createElement("div");
    box.className = "bar";

    let fill = document.createElement("div");
    fill.className = "fill";
    fill.style.height = (10 + m.count*3) + "px";

    box.appendChild(fill);
    box.innerHTML += m.month;

    year.appendChild(box);
});

});