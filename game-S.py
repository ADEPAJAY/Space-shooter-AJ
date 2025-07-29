
import tkinter as tk
import random
import time

SCALE = 1.2
WIDTH, HEIGHT = 480, 720
ENEMY_SPEED = 3
BULLET_SPEED = 10
MAX_MISSES = 4

class PowerUp:
    TYPES = ["double_bullets", "rapid_fire", "shield"]
    COLORS = {
        "double_bullets": "cyan",
        "rapid_fire": "orange",
        "shield": "blue"
    }

    def __init__(self, canvas, x, y):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.type = random.choice(PowerUp.TYPES)
        self.size = 24
        self.id = canvas.create_oval(x - self.size//2, y - self.size//2,
                                     x + self.size//2, y + self.size//2,
                                     fill=PowerUp.COLORS[self.type])
        self.speed = 3

    def update(self):
        self.y += self.speed
        if self.y > HEIGHT + self.size:
            self.canvas.delete(self.id)
            return False
        self.canvas.coords(self.id, self.x - self.size//2, self.y - self.size//2,
                           self.x + self.size//2, self.y + self.size//2)
        return True

    def destroy(self):
        self.canvas.delete(self.id)


class Explosion:
    def __init__(self, canvas, x, y):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.size = 12
        self.max_size = 60
        self.id = canvas.create_oval(x - self.size, y - self.size, x + self.size, y + self.size, fill="yellow")
        self.growth_rate = 6

    def update(self):
        self.size += self.growth_rate
        if self.size >= self.max_size:
            self.canvas.delete(self.id)
            return False
        gray_val = int(255 * (1 - self.size / self.max_size))
        color = f"#{gray_val:02x}{gray_val:02x}00"
        self.canvas.itemconfig(self.id, fill=color)
        self.canvas.coords(self.id, self.x - self.size, self.y - self.size, self.x + self.size, self.y + self.size)
        return True


class ShooterGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Space Blaster by AJ")

        self.player_name = ""
        self.missed = 0
        self.score = 0
        self.bullets = []
        self.enemies = []
        self.big_enemies = []
        self.explosions = []
        self.powerups = []
        self.active_powerup = None
        self.powerup_end_time = 0
        self.can_shoot = True
        self.last_shot_time = 0
        self.shoot_cooldown = 400
        self.shield_active = False
        self.game_over_flag = False

        self.load_images()
        self.start_screen()

    def load_images(self):
        self.player_img = tk.PhotoImage(file="spc1.png")
        self.enemy_img = tk.PhotoImage(file="spc2.png")
        self.bullet_img = tk.PhotoImage(file="bullet.png")
        self.big_enemy_imgs = [
            tk.PhotoImage(file="big_enemy.png"),
            tk.PhotoImage(file="big_enemy2.png"),
            tk.PhotoImage(file="big_enemy3.png")
        ]

    def start_screen(self):
        self.start_frame = tk.Frame(self.root, bg="#001022")
        self.start_frame.pack(fill="both", expand=True)

        tk.Label(self.start_frame, text="Enter Your Name:", font=("Consolas", 16), bg="#001022", fg="white").pack(pady=20)
        self.name_entry = tk.Entry(self.start_frame, font=("Consolas", 14))
        self.name_entry.pack(pady=10)

        tk.Button(self.start_frame, text="Start Game", font=("Consolas", 14), bg="#00adb5", fg="white",
                  command=self.start_game).pack(pady=20)

    def start_game(self):
        self.player_name = self.name_entry.get() or "Player"
        self.start_frame.destroy()

        self.canvas = tk.Canvas(self.root, width=WIDTH, height=HEIGHT, bg="#001022", highlightthickness=0)
        self.canvas.pack()

        self.stars = []
        for _ in range(100):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            size = random.randint(1, 3)
            star_id = self.canvas.create_oval(x, y, x+size, y+size, fill="white", outline="")
            self.stars.append({'id': star_id, 'size': size, 'x': x, 'y': y, 'twinkle_dir': 1})

        self.animate_stars()

        self.player = self.canvas.create_image(WIDTH//2, HEIGHT - int(80 * SCALE), image=self.player_img)


        self.score_label = tk.Label(self.root, text=f"Score: {self.score}", font=("Consolas", 14), bg="#001022", fg="white")
        self.score_label.place(x=10, y=5)

        # ✅ Replaces the Label — new canvas text for power-up info
        self.powerup_text = self.canvas.create_text(WIDTH//2, HEIGHT - 30, text="", font=("Consolas", 14), fill="cyan")

        self.root.bind("<Left>", self.move_left)
        self.root.bind("<Right>", self.move_right)
        self.root.bind("<space>", self.shoot)

        self.spawn_enemy()
        self.update()

    def animate_stars(self):
        for star in self.stars:
            new_size = star['size'] + star['twinkle_dir'] * 0.1
            if new_size > 3:
                star['twinkle_dir'] = -1
            elif new_size < 1:
                star['twinkle_dir'] = 1
            star['size'] = new_size
            x, y = star['x'], star['y']
            self.canvas.coords(star['id'], x, y, x + new_size, y + new_size)

        self.root.after(100, self.animate_stars)

    def move_left(self, event):
        x, y = self.canvas.coords(self.player)
        if x > 40:
            self.canvas.move(self.player, -20, 0)

    def move_right(self, event):
        x, y = self.canvas.coords(self.player)
        if x < WIDTH - 40:
            self.canvas.move(self.player, 20, 0)

    def shoot(self, event):
        now = int(time.time() * 1000)
        if not self.can_shoot and (now - self.last_shot_time) < self.shoot_cooldown:
            return
        self.last_shot_time = now

        px, py = self.canvas.coords(self.player)
        if self.active_powerup == "double_bullets":
            bullet1 = self.canvas.create_image(px - 18, py - 48, image=self.bullet_img)
            bullet2 = self.canvas.create_image(px + 18, py - 48, image=self.bullet_img)
            self.bullets.append(bullet1)
            self.bullets.append(bullet2)
        else:
            bullet = self.canvas.create_image(px, py - 48, image=self.bullet_img)
            self.bullets.append(bullet)

    def spawn_enemy(self):
        x = random.randint(40, WIDTH - 40)
        enemy = self.canvas.create_image(x, 30, image=self.enemy_img)
        self.enemies.append(enemy)
        self.root.after(1500, self.spawn_enemy)

    def spawn_big_enemies(self):
        if self.score > 0 and self.score % 150 == 0 and not self.big_enemies:
            for i, health in enumerate([10, 15, 20]):
                x = 100 + i * 100
                big_enemy_id = self.canvas.create_image(x, 50, image=self.big_enemy_imgs[i])
                health_bar_bg = self.canvas.create_rectangle(x - 48, 10, x + 48, 20, fill="red")
                health_bar_fg = self.canvas.create_rectangle(x - 48, 10, x - 48 + 96, 20, fill="green")
                self.big_enemies.append({
                    'id': big_enemy_id,
                    'health': health,
                    'max_health': health,
                    'health_bar_bg': health_bar_bg,
                    'health_bar_fg': health_bar_fg,
                    'x': x,
                    'y': 50,
                    'speed': 1,
                    'img_index': i
                })

    def update(self):
        if self.game_over_flag:
            return

        if self.missed >= MAX_MISSES:
            self.game_over()
            return

        for bullet in self.bullets[:]:
            self.canvas.move(bullet, 0, -BULLET_SPEED)
            bx1, by1 = self.canvas.coords(bullet)
            if by1 < 0:
                self.canvas.delete(bullet)
                self.bullets.remove(bullet)

        for enemy in self.enemies[:]:
            self.canvas.move(enemy, 0, ENEMY_SPEED)
            ex, ey = self.canvas.coords(enemy)
            if ey > HEIGHT:
                self.canvas.delete(enemy)
                self.enemies.remove(enemy)
                self.missed += 1
            else:
                for bullet in self.bullets[:]:
                    bx, by = self.canvas.coords(bullet)
                    if abs(bx - ex) < 20 and abs(by - ey) < 20:
                        self.enemy_killed(ex, ey)
                        self.canvas.delete(bullet)
                        self.bullets.remove(bullet)
                        self.canvas.delete(enemy)
                        self.enemies.remove(enemy)
                        self.score += 10
                        self.score_label.config(text=f"Score: {self.score}")
                        break

        self.spawn_big_enemies()

        for big_enemy_dict in self.big_enemies[:]:
            dx, dy = 0, big_enemy_dict['speed']
            self.canvas.move(big_enemy_dict['id'], dx, dy)
            self.canvas.move(big_enemy_dict['health_bar_bg'], dx, dy)
            self.canvas.move(big_enemy_dict['health_bar_fg'], dx, dy)

            bex, bey = self.canvas.coords(big_enemy_dict['id'])
            big_enemy_dict['x'], big_enemy_dict['y'] = bex, bey

            x1, y1, x2, y2 = self.canvas.coords(big_enemy_dict['health_bar_bg'])
            max_width = x2 - x1
            new_width = max_width * (big_enemy_dict['health'] / big_enemy_dict['max_health'])
            self.canvas.coords(big_enemy_dict['health_bar_fg'], x1, y1, x1 + new_width, y2)

            if bey > HEIGHT + 50:
                self.canvas.delete(big_enemy_dict['id'])
                self.canvas.delete(big_enemy_dict['health_bar_bg'])
                self.canvas.delete(big_enemy_dict['health_bar_fg'])
                self.big_enemies.remove(big_enemy_dict)
                self.missed += 1
                continue

            for bullet in self.bullets[:]:
                bx, by = self.canvas.coords(bullet)
                if abs(bx - bex) < 40 and abs(by - bey) < 40:
                    big_enemy_dict['health'] -= 1
                    self.canvas.delete(bullet)
                    self.bullets.remove(bullet)
                    if big_enemy_dict['health'] <= 0:
                        self.create_explosion(bex, bey)
                        self.canvas.delete(big_enemy_dict['id'])
                        self.canvas.delete(big_enemy_dict['health_bar_bg'])
                        self.canvas.delete(big_enemy_dict['health_bar_fg'])
                        self.big_enemies.remove(big_enemy_dict)
                        self.score += 50
                        self.score_label.config(text=f"Score: {self.score}")
                        self.enemy_killed(bex, bey)
                        if self.score >= 1150:
                            self.win_game()
                    break

        for powerup in self.powerups[:]:
            if not powerup.update():
                self.powerups.remove(powerup)

        px, py = self.canvas.coords(self.player)
        player_size = 40

        for powerup in self.powerups[:]:
            if abs(px - powerup.x) < player_size and abs(py - powerup.y) < player_size:
                self.activate_powerup(powerup.type)
                powerup.destroy()
                self.powerups.remove(powerup)

        if self.active_powerup and time.time() > self.powerup_end_time:
            self.deactivate_powerup()

        for explosion in self.explosions[:]:
            if not explosion.update():
                self.explosions.remove(explosion)

        self.root.after(30, self.update)

    def enemy_killed(self, x, y):
        if random.random() < 0.25:
            powerup = PowerUp(self.canvas, x, y)
            self.powerups.append(powerup)

    def create_explosion(self, x, y):
        explosion = Explosion(self.canvas, x, y)
        self.explosions.append(explosion)

    def activate_powerup(self, powerup_type):
        self.active_powerup = powerup_type
        self.powerup_end_time = time.time() + 5
        # ✅ Set canvas text instead of label
        self.canvas.itemconfig(self.powerup_text, text=f"Power-up: {powerup_type.replace('_', ' ').title()}")

        if powerup_type == "rapid_fire":
            self.shoot_cooldown = 150
        elif powerup_type == "shield":
            self.shield_active = True
        elif powerup_type == "double_bullets":
            pass

    def deactivate_powerup(self):
        self.active_powerup = None
        self.canvas.itemconfig(self.powerup_text, text="")  # ✅ Clear canvas text
        self.shoot_cooldown = 400
        self.shield_active = False

    def game_over(self):
        self.game_over_flag = True
        self.canvas.delete("all")
        self.score_label.pack_forget()
        self.canvas.create_text(WIDTH//2, HEIGHT//2, text=f"GAME OVER\nScore: {self.score}",
                                font=("Consolas", 24), fill="red")

    def win_game(self):
        self.game_over_flag = True
        self.canvas.delete("all")
        self.score_label.pack_forget()
        self.canvas.create_text(WIDTH//2, HEIGHT//2, text=f"YOU WIN!\nScore: {self.score}",
                                font=("Consolas", 24), fill="green")

def main():
    root = tk.Tk()
    screen_width = root.winfo_screenwidth()

    x_pos = int((screen_width - WIDTH) / 2)
    y_pos = 20  # 20 pixels from the top of the screen

    root.geometry(f"{WIDTH}x{HEIGHT}+{x_pos}+{y_pos}")
    
    game = ShooterGame(root)
    root.mainloop()

if __name__ == "__main__":
    main()

