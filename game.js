const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");

const scoreEl = document.getElementById("score");
const livesEl = document.getElementById("lives");
const levelEl = document.getElementById("level");
const bestEl = document.getElementById("best");
const pauseBtn = document.getElementById("pause");
const restartBtn = document.getElementById("restart");

const width = canvas.width;
const height = canvas.height;
const BEST_SCORE_KEY = "spaceShooterBestScore";

const input = {
  left: false,
  right: false,
  up: false,
  down: false,
  shoot: false,
};

const state = {
  score: 0,
  bestScore: Number(localStorage.getItem(BEST_SCORE_KEY) || 0),
  lives: 3,
  level: 1,
  gameOver: false,
  paused: false,
  lastTime: 0,
  shootCooldown: 0,
  spawnTimer: 0,
  invincibleTimer: 0,
  stars: Array.from({ length: 80 }, () => ({
    x: Math.random() * width,
    y: Math.random() * height,
    speed: 40 + Math.random() * 100,
    size: Math.random() * 2 + 1,
  })),
  explosions: [],
  player: {
    x: width / 2,
    y: height - 80,
    w: 36,
    h: 48,
    speed: 300,
  },
  bullets: [],
  enemies: [],
};

function syncHud() {
  scoreEl.textContent = String(state.score);
  livesEl.textContent = String(state.lives);
  levelEl.textContent = String(state.level);
  bestEl.textContent = String(state.bestScore);
}

function asteroidShape(radius) {
  const points = 8;
  return Array.from({ length: points }, (_, i) => {
    const theta = (Math.PI * 2 * i) / points;
    const variance = radius * (0.74 + Math.random() * 0.34);
    return { x: Math.cos(theta) * variance, y: Math.sin(theta) * variance };
  });
}

function resetGame() {
  state.score = 0;
  state.lives = 3;
  state.level = 1;
  state.gameOver = false;
  state.paused = false;
  state.shootCooldown = 0;
  state.spawnTimer = 0;
  state.invincibleTimer = 1;
  state.player.x = width / 2;
  state.player.y = height - 80;
  state.bullets = [];
  state.enemies = [];
  state.explosions = [];

  pauseBtn.textContent = "暂停";
  restartBtn.hidden = true;
  syncHud();

  state.lastTime = performance.now();
  requestAnimationFrame(loop);
}

function spawnEnemy() {
  const radius = 14 + Math.random() * 22;
  const speedFactor = 1 + Math.min(1.2, state.level * 0.11);

  state.enemies.push({
    x: radius + Math.random() * (width - radius * 2),
    y: -radius - Math.random() * 80,
    r: radius,
    speed: (70 + Math.random() * 110) * speedFactor,
    spin: (Math.random() - 0.5) * 1.8,
    angle: 0,
    hp: Math.ceil(radius / 12),
    shape: asteroidShape(radius),
  });
}

function shoot() {
  state.bullets.push({
    x: state.player.x,
    y: state.player.y - 28,
    vy: -460,
    w: 4,
    h: 15,
  });
}

function createExplosion(x, y, size, color = "#ffd166") {
  state.explosions.push({
    x,
    y,
    size,
    life: 0.28,
    maxLife: 0.28,
    color,
  });
}

function damagePlayer() {
  if (state.invincibleTimer > 0) {
    return;
  }
  state.lives -= 1;
  state.invincibleTimer = 1.2;
  createExplosion(state.player.x, state.player.y, 24, "#ff6b6b");

  if (state.lives <= 0) {
    state.gameOver = true;
    restartBtn.hidden = false;
    pauseBtn.textContent = "暂停";
    input.shoot = false;

    if (state.score > state.bestScore) {
      state.bestScore = state.score;
      localStorage.setItem(BEST_SCORE_KEY, String(state.bestScore));
    }
  }

  syncHud();
}

function levelUpByScore() {
  const newLevel = Math.floor(state.score / 120) + 1;
  if (newLevel !== state.level) {
    state.level = newLevel;
    syncHud();
  }
}

function update(dt) {
  if (state.gameOver || state.paused) {
    return;
  }

  const p = state.player;
  const moveX = (input.right ? 1 : 0) - (input.left ? 1 : 0);
  const moveY = (input.down ? 1 : 0) - (input.up ? 1 : 0);

  p.x += moveX * p.speed * dt;
  p.y += moveY * p.speed * dt;
  p.x = Math.max(p.w / 2, Math.min(width - p.w / 2, p.x));
  p.y = Math.max(p.h / 2, Math.min(height - p.h / 2, p.y));

  state.shootCooldown -= dt;
  const rapidBonus = Math.min(0.08, (state.level - 1) * 0.005);
  const fireInterval = 0.18 - rapidBonus;
  if (input.shoot && state.shootCooldown <= 0) {
    shoot();
    state.shootCooldown = fireInterval;
  }

  state.spawnTimer -= dt;
  if (state.spawnTimer <= 0) {
    spawnEnemy();
    const base = 0.95 - state.level * 0.06;
    state.spawnTimer = Math.max(0.26, base + Math.random() * 0.25);
  }

  if (state.invincibleTimer > 0) {
    state.invincibleTimer -= dt;
  }

  for (const star of state.stars) {
    star.y += star.speed * dt;
    if (star.y > height) {
      star.y = -3;
      star.x = Math.random() * width;
    }
  }

  for (const bullet of state.bullets) {
    bullet.y += bullet.vy * dt;
  }
  state.bullets = state.bullets.filter((b) => b.y + b.h > 0);

  for (const enemy of state.enemies) {
    enemy.y += enemy.speed * dt;
    enemy.angle += enemy.spin * dt;
  }

  for (const bullet of state.bullets) {
    for (const enemy of state.enemies) {
      const dx = bullet.x - enemy.x;
      const dy = bullet.y - enemy.y;
      if (dx * dx + dy * dy <= enemy.r * enemy.r) {
        bullet.y = -100;
        enemy.hp -= 1;
        if (enemy.hp <= 0) {
          enemy.y = height + 120;
          createExplosion(enemy.x, enemy.y, enemy.r + 6);
          state.score += 10 + state.level * 2;
          if (state.score > state.bestScore) {
            state.bestScore = state.score;
          }
          syncHud();
          levelUpByScore();
        }
      }
    }
  }

  state.enemies = state.enemies.filter((e) => e.y - e.r <= height + 40 && e.hp > 0);

  for (const enemy of state.enemies) {
    const dx = Math.abs(enemy.x - p.x);
    const dy = Math.abs(enemy.y - p.y);
    if (dx < enemy.r + p.w * 0.36 && dy < enemy.r + p.h * 0.36) {
      enemy.y = height + 80;
      damagePlayer();
    } else if (enemy.y - enemy.r > height) {
      enemy.y = height + 80;
      damagePlayer();
    }
  }

  for (const exp of state.explosions) {
    exp.life -= dt;
  }
  state.explosions = state.explosions.filter((exp) => exp.life > 0);
  state.enemies = state.enemies.filter((e) => e.y <= height + 50);
}

function drawPlayer() {
  const p = state.player;
  ctx.save();
  ctx.translate(p.x, p.y);

  if (state.invincibleTimer > 0 && Math.floor(state.invincibleTimer * 12) % 2 === 0) {
    ctx.globalAlpha = 0.5;
  }

  ctx.fillStyle = "#8fd8ff";
  ctx.beginPath();
  ctx.moveTo(0, -p.h / 2);
  ctx.lineTo(p.w / 2, p.h / 2);
  ctx.lineTo(0, p.h / 3);
  ctx.lineTo(-p.w / 2, p.h / 2);
  ctx.closePath();
  ctx.fill();

  ctx.fillStyle = "#ffd166";
  ctx.beginPath();
  ctx.moveTo(-6, p.h / 2 - 3);
  ctx.lineTo(0, p.h / 2 + 12);
  ctx.lineTo(6, p.h / 2 - 3);
  ctx.closePath();
  ctx.fill();

  ctx.restore();
}

function drawOverlay(text, subText = "") {
  ctx.fillStyle = "rgba(0,0,0,0.55)";
  ctx.fillRect(0, 0, width, height);

  ctx.fillStyle = "#fff";
  ctx.font = "bold 44px sans-serif";
  ctx.textAlign = "center";
  ctx.fillText(text, width / 2, height / 2 - 30);

  if (subText) {
    ctx.font = "22px sans-serif";
    ctx.fillText(subText, width / 2, height / 2 + 16);
  }
}

function draw() {
  ctx.clearRect(0, 0, width, height);

  for (const star of state.stars) {
    ctx.fillStyle = "rgba(255,255,255,0.9)";
    ctx.fillRect(star.x, star.y, star.size, star.size);
  }

  drawPlayer();

  ctx.fillStyle = "#87f2ff";
  for (const bullet of state.bullets) {
    ctx.fillRect(bullet.x - bullet.w / 2, bullet.y - bullet.h / 2, bullet.w, bullet.h);
  }

  for (const enemy of state.enemies) {
    ctx.save();
    ctx.translate(enemy.x, enemy.y);
    ctx.rotate(enemy.angle);
    ctx.fillStyle = "#9a7b4f";
    ctx.beginPath();
    enemy.shape.forEach((pt, index) => {
      if (index === 0) {
        ctx.moveTo(pt.x, pt.y);
      } else {
        ctx.lineTo(pt.x, pt.y);
      }
    });
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }

  for (const exp of state.explosions) {
    const progress = 1 - exp.life / exp.maxLife;
    ctx.save();
    ctx.globalAlpha = 1 - progress;
    ctx.strokeStyle = exp.color;
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.arc(exp.x, exp.y, exp.size * (0.6 + progress), 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();
  }

  if (state.paused && !state.gameOver) {
    drawOverlay("已暂停", "点击“继续”或按 P 继续");
  }

  if (state.gameOver) {
    drawOverlay("游戏结束", `最终得分: ${state.score}`);
  }
}

function loop(ts) {
  const dt = Math.min(0.033, (ts - state.lastTime) / 1000);
  state.lastTime = ts;
  update(dt);
  draw();
  if (!state.gameOver) {
    requestAnimationFrame(loop);
  }
}

function togglePause() {
  if (state.gameOver) {
    return;
  }
  state.paused = !state.paused;
  pauseBtn.textContent = state.paused ? "继续" : "暂停";
  if (!state.paused) {
    state.lastTime = performance.now();
    requestAnimationFrame(loop);
  } else {
    draw();
  }
}

window.addEventListener("keydown", (e) => {
  if (e.code === "ArrowLeft" || e.code === "KeyA") input.left = true;
  if (e.code === "ArrowRight" || e.code === "KeyD") input.right = true;
  if (e.code === "ArrowUp" || e.code === "KeyW") input.up = true;
  if (e.code === "ArrowDown" || e.code === "KeyS") input.down = true;

  if (e.code === "Space") {
    input.shoot = true;
    e.preventDefault();
  }

  if (e.code === "KeyP") {
    togglePause();
  }
});

window.addEventListener("keyup", (e) => {
  if (e.code === "ArrowLeft" || e.code === "KeyA") input.left = false;
  if (e.code === "ArrowRight" || e.code === "KeyD") input.right = false;
  if (e.code === "ArrowUp" || e.code === "KeyW") input.up = false;
  if (e.code === "ArrowDown" || e.code === "KeyS") input.down = false;
  if (e.code === "Space") input.shoot = false;
});

pauseBtn.addEventListener("click", togglePause);
restartBtn.addEventListener("click", resetGame);

syncHud();
resetGame();
