var c = document.getElementById("activity");
var ctx = c.getContext("2d");

var LIVE_PARTICLES=0;

window.requestAnimFrame =
    window.requestAnimationFrame ||
    window.webkitRequestAnimationFrame ||
    window.mozRequestAnimationFrame ||
    window.oRequestAnimationFrame ||
    window.msRequestAnimationFrame ||
    function(callback) {
        window.setTimeout(callback, 1000 / 30);
    };

MAX_PARTICLES=1000
MIN_DECAY_RATE = 0.005;
MAX_DECAY_RATE = 0.010;
MIN_SPEED=0.1
MAX_SPEED = 4
MIN_SIZE = 5
MAX_SIZE = 15
MAN_DOWN=false

particles = []

palette = [{"red": 235, "green": 73, "blue": 113},
    {"red": 0, "green": 185, "blue": 190},
    {"red": 179, "green": 108, "blue": 219},
    {"red": 0, "green": 116, "blue": 224}]


var Particle = function(index){
    this.x = c.width/2;
    this.y = c.height/2;
    this.red = this.green = this.blue = 0;

    col_index = (index % palette.length);
    this.red = palette[col_index].red;
    this.green = palette[col_index].green;
    this.blue = palette[col_index].blue;
    this.id = index;
    this.active = true;


    var xdir = 0.5-Math.random();
    if (xdir < 0){
        this.xspeed = -MIN_SPEED - (Math.random() * (MAX_SPEED - MIN_SPEED));
    }
    else
    {
        this.xspeed = MIN_SPEED + (Math.random() * (MAX_SPEED - MIN_SPEED));
    }
    var ydir = 0.5-Math.random();
    if (ydir < 0){
        this.yspeed = -MIN_SPEED - (Math.random() * (MAX_SPEED - MIN_SPEED));
    }
    else
    {
        this.yspeed = MIN_SPEED + (Math.random() * (MAX_SPEED - MIN_SPEED));
    }
    this.yspeed = (0.5-Math.random()) * MAX_SPEED;
    this.size = MIN_SIZE + (Math.random() * (MAX_SIZE - MIN_SIZE));

    this.alpha = 1;
    this.decay = MIN_DECAY_RATE + (Math.random() * (MAX_DECAY_RATE - MIN_DECAY_RATE));
    this.index = index;

    this.draw = function(){
        if (this.active) {
            ctx.fillStyle = 'rgba(' + this.red + ',' + this.green + ',' + this.blue + ',' + this.alpha+')';
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();
        }
    }


    this.update = function(){
        if (this.active &&
            (!MAN_DOWN || (this.index % 3 != 0))) {
            this.alpha -= this.decay;
            this.x += this.xspeed;
            this.y += this.yspeed;
            if (this.x >= c.width || this.x <= 0 ||
                this.y >= c.height || this.y <= 0 ||
                this.alpha <= 0){
                this.active = false;
            }
        }
        if (!this.active && this.index < LIVE_PARTICLES) {
            particles[this.index] = new Particle(this.index);
        }
    }
};


function drawCircles(){
    ctx.clearRect(0, 0, c.width,c.height);
    for (i=0;  i < MAX_PARTICLES;i++)
    {
        particles[i].update();
        particles[i].draw();
    }
}

function loop() {
    drawCircles();
    requestAnimFrame(loop);
}

for (i=0; i< MAX_PARTICLES;i++)
{
    particles[i] = new Particle(i);
}
loop();