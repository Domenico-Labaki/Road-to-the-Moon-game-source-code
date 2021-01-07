#-------------------------------------------------------------------------------
# Name:        road_to_the_moon
#
# Purpose:     Game Off 2020
#
# Author:      Domenico Labaki
#
# Created:     02/11/2020
# Copyright:   (c) Domenico Labaki 2020
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import pygame, random, math, os, time

image_src = r'.\images'+'/'

_image_library = {}
def get_image(path):
        global _image_library
        image = _image_library.get(path)
        if image == None:
                canonicalized_path = path.replace('/', os.sep).replace('\\', os.sep)
                image = pygame.image.load(canonicalized_path)
                _image_library[path] = image
        return image

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()

def render_number(number,startX,y):
    number_str = str(number)
    for num in range(len(number_str)):
        screen.blit(get_image(image_src+'nums/'+number_str[num]+'.png'),(startX+num*40,y))

def slide_in(location,max_pos,speed):
    if location[0] < max_pos:
        location[0] += speed
    return location

def move_player(location,delay):
    pressed = pygame.key.get_pressed()
    if pressed[pygame.K_UP]:
        location[1] -= yVel
        if location[1] < 80:
           location[1] = 80
        else:
            delay += yVel
    if pressed[pygame.K_DOWN]:
        location[1] += yVel
        if location[1] > 510: #560-50=510 this is window height - player height
            location[1] = 510
        else:
            delay -= yVel
    return location,delay

def spawn_object(cooldown, data):
    if cooldown > 0:
        cooldown -= 1
    else:
        data.append([1000,random.randint(100,500)])
        cooldown = 100
    return cooldown, data

def move_object(object_list, objects_to_delete):
    for i in range(len(object_list)):
        location = object_list[i]
        if location[0] < -69:
            objects_to_delete.append(location)
        else:
            location[0] -= 7
        object_list[i] = location
    return object_list, objects_to_delete

def rotate_object(object_list,material,angle):
    object_hitboxes = []
    for i in range(len(object_list)):
        straight = get_image(image_src+material+'.png')
        rotated = pygame.transform.rotate(straight,angle)
        if material == 'meteor': side = 50
        elif material == 'crystal': side = 30
        location = object_list[i]
        item = screen.blit(rotated,(location[0]-int(rotated.get_width()/2),location[1]-int(rotated.get_height()/2)))
        hitbox = pygame.Rect(location[0]-side/2,location[1]-side/2,side,side)
        object_hitboxes.append(hitbox)
    return object_hitboxes

def object_collision(object_list,object_hitboxes,objects_to_delete,particles,material):
    global activity, score, lives, transition, transitionY, transition_timer, catch_crystal, player_gets_hit, player_dies
    for i in range(len(object_hitboxes)):
        location = object_list[i]
        if player_hitbox.colliderect(object_hitboxes[i]):
            if material == 'meteor':
                color = (150,150,150)
            elif material == 'crystal':
                color = (171, 0, 157)
            for p in range(random.randint(4,10)):
                particles.append([[object_hitboxes[i][0]+object_hitboxes[i][2]/2,object_hitboxes[i][1]+object_hitboxes[i][3]/2],[random.randint(-3,3),random.randint(-3,3)],100,color])
            objects_to_delete.append(location)
            if material == 'meteor':
                lives -= 1
                if lives < 1:
                    player_dies.play()
                    activity = 'menu'
                    transition = 'lose'
                    transitionY = 0
                    transition_timer = 120
                else:
                    player_gets_hit.play()
            elif material == 'crystal':
                score += 10
                catch_crystal.play()
    for m in range(len(objects_to_delete)):
        object_list.remove(objects_to_delete[m])
    objects_to_delete.clear()
    return object_list, objects_to_delete, particles

def divide_in_waves(total,waves):
    wave_list = []
    single_wave = math.floor(total/waves)
    total_check = 0
    for w in range(waves):
        wave_list.append(single_wave)
        total_check += single_wave
    if total_check < total:
        bonus = total-total_check
        wave_list[waves-1] += bonus
    return wave_list

def spawn_enemies(enemy_list,wave_list,wave,total_enemy_hp,enemy_type):
    if len(enemy_list) < 1 and enemy_cooldown == 0:
        wave += 1
        if wave < len(wave_list)+1:
            enemies = wave_list[wave-1]
            y = 560/(enemies+1)
            if enemy_type == 'mover':
                direction = 'up'
            else:
                direction = ''
            for w in range(enemies):
                ogYpos = 10+y*(w+1)
                enemy_list.append([1000,ogYpos,total_enemy_hp,ogYpos-45,ogYpos+45,direction])
    return enemy_list,wave

def move_enemies(enemy_list):
    for e in range(len(enemy_list)):
        data = enemy_list[e]
        if data[0] > 650:
            data[0] -= 5
        if data[5] == 'up':
            data[1] -= 1
        elif data[5] == 'down':
            data[1] += 1
        if data[1] < data[3]:
            data[5] = 'down'
        elif data[1] > data[4]:
            data[5] = 'up'
        enemy_list[e] = data
    return enemy_list

def spawn_laser(laser_list,location):
    laser_list.append([location[0]+100,location[1]+25])
    return laser_list

def spawn_enemy_laser(enemy_laser_list,location,total_lasers):
    l = random.randint(1,total_lasers)
    enemy_laser_list.append([location[0],location[1]+25*l])
    return enemy_laser_list

def move_lasers(laser_list,owner):
    lasers_to_delete = []
    for l in range(len(laser_list)):
        location = laser_list[l]
        if location[0] > 999 or location[0] < -25:
            lasers_to_delete.append(location)
        else:
            if owner == 'player':
                location[0] += 15
            elif owner == 'enemy':
                location[0] -= 7
    for l in range(len(lasers_to_delete)):
        laser_list.remove(lasers_to_delete[l])
    lasers_to_delete.clear()
    return laser_list

def laser_collision(laser_list,enemy_list,player_hitbox,enemy_type,owner,particles):
    global score, lives, activity, transition, transitionY, transition_timer, player_gets_hit, player_dies, enemy_gets_hit, enemy_dies, boss_dies
    enemies_to_delete = []
    lasers_to_delete = []
    laser = get_image(image_src+owner+'_laser.png')
    enemy = get_image(image_src+'enemies/'+enemy_type+'.png')
    for l in range(len(laser_list)):
        laser_location = laser_list[l]
        laser_hitbox = pygame.Rect(laser_location[0],laser_location[1],laser.get_width(),laser.get_height())
        if owner == 'player':
            for e in range(len(enemy_list)):
                enemy_data = enemy_list[e]
                enemy_hitbox = pygame.Rect(enemy_data[0],enemy_data[1],enemy.get_width(),enemy.get_height())
                if laser_hitbox.colliderect(enemy_hitbox):
                    enemy_data[2] -= 1
                    enemy_list[e] = enemy_data
                    if enemy_data[2] < 1:
                        if enemy_type == 'boss':
                            boss_dies.play()
                            score += 100
                        else:
                            enemy_dies.play()
                            score += 20
                        if not enemy_data in enemies_to_delete:
                            enemies_to_delete.append(enemy_data)
                    else:
                        enemy_gets_hit.play()
                    lasers_to_delete.append(laser_location)
                    for p in range(random.randint(4,10)):
                        particles.append([[math.floor(laser_location[0]+laser.get_width()),math.floor(laser_location[1])],[random.randint(-3,3),random.randint(-3,3)],100,(0, 212, 106)])
        elif owner == 'enemy':
            if laser_hitbox.colliderect(player_hitbox):
                lives -= 1
                if lives < 1:
                    player_dies.play()
                    activity = 'menu'
                    transition = 'lose'
                    transitionY = 0
                    transition_timer = 120
                else:
                    player_gets_hit.play()
                if score > 4:
                    score -= 5
                lasers_to_delete.append(laser_location)
                for p in range(random.randint(4,10)):
                    particles.append([[math.floor(laser_location[0]),math.floor(laser_location[1])],[random.randint(-3,3),random.randint(-3,3)],100,(255,100,0)])
    for l in range(len(lasers_to_delete)):
        laser_list.remove(lasers_to_delete[l])
    lasers_to_delete.clear()
    for e in range(len(enemies_to_delete)):
        enemy_list.remove(enemies_to_delete[e])
    enemies_to_delete.clear()
    return laser_list, enemy_list, particles

def draw_fire(location,min_side,delay):
    colors = [[245,228,0],[245,216,0],[245,170,0],[245,118,0],[245,0,0]]
    for f in range(5):
        side = min_side*(f+1)
        x = location[0] - side
        for i in range(f):
            x -= min_side*(i+1)
        y = location[1]+36-(side/2)
        y += delay*(f/4)
        rect = pygame.Rect(x,y,side,side)
        pygame.draw.rect(screen,colors[f],rect)
        pygame.draw.rect(screen,(70,70,70),rect,2)

def draw_particles(particles):
    particles_to_delete = []
    for p in range(len(particles)):
        particle_data = particles[p]
        pygame.draw.circle(screen,particle_data[3],particle_data[0],math.floor(particle_data[2]/10))
        particle_location = particle_data[0]
        particle_velocity = particle_data[1]
        particle_location[0] += particle_velocity[0]
        particle_location[1] += particle_velocity[1]
        particle_data = [particle_location,particle_velocity,particle_data[2]-1,particle_data[3]]
        particles[p] = particle_data
        if particle_data[2] < 0:
            particles_to_delete.append(particle_data)
        elif particle_location[1] < 80:
            particles_to_delete.append(particle_data)
    for p in range(len(particles_to_delete)):
        particles.remove(particles_to_delete[p])
    particles_to_delete.clear()
    return particles

def addlife(lives, add_count):
    lives += add_count
    if lives > 6:
        lives -= lives-6
    return lives

pygame.display.set_icon(get_image(image_src+'window_icon.ico'))
screen = pygame.display.set_mode((1000, 560))
pygame.display.set_caption('Road to the Moon')

bg_scrollX = 0

player_location = [-100,255]
yVel = 4
xVel = -100 #for slide in effect
delay = 0 #for fire animation

activity = 'menu'
transition = ''
transitionY = -560
transition_timer = 60

meteor_list = []
meteor_location = []
meteors_to_delete = []
meteor_hitboxes = []

crystal_list = []
crystal_location = []
crystals_to_delete = []
crystal_hitboxes = []

meteor_check = [0,0,0,0,0,0,1,1,1,1]
level_total_enemies = [7,14,18,10,16,1,25,20,28,1]
level_total_waves = [3,3,3,3,4,1,5,5,7,1]
level_enemy_types = ['ufo','ufo','ufo','mover','mover','boss','ufo','mover','mover','boss']
wave_list = []
enemy_list = []

enemy_cooldown = 0
enemy_shoot_cooldown = 120
wave = 0

laser_list = []
shoot_cooldown = 0
total_player_shots = 1

particles = []

angle = 0
object_spawn_cooldown = 180

lives = 6
score = 0
level = 1

total_levels = len(level_enemy_types)

pause = False
won = False

sound_src = r'.\sounds'+'/'

player_shot = pygame.mixer.Sound(sound_src+'sfx_weapon_singleshot7.wav')
enemy_shot = pygame.mixer.Sound(sound_src+'sfx_wpn_laser6.wav')
catch_crystal = pygame.mixer.Sound(sound_src+'sfx_coin_double1.wav')
player_gets_hit = pygame.mixer.Sound(sound_src+'sfx_sounds_damage1.wav')
player_dies = pygame.mixer.Sound(sound_src+'sfx_exp_double2.wav')
enemy_gets_hit = pygame.mixer.Sound(sound_src+'sfx_damage_hit5.wav')
enemy_dies = pygame.mixer.Sound(sound_src+'sfx_exp_shortest_soft1.wav')
boss_dies = pygame.mixer.Sound(sound_src+'sfx_exp_long6.wav')
button_click = pygame.mixer.Sound(sound_src+'sfx_menu_select2.wav')

pygame.mixer.music.load(r'.\music\underclocked_eric_skiff.mp3')
pygame.mixer.music.play(-1)

running = True
clock = pygame.time.Clock()
while running:
    screen.fill((255, 255, 255))
    #bg
    if bg_scrollX < -1000:
        bg_scrollX = 0
    else:
        bg_scrollX -= 2
    screen.blit(get_image(image_src+'bg.png'), (bg_scrollX,0))
    screen.blit(get_image(image_src+'bg.png'), (bg_scrollX+1000,0))

    if activity == 'menu':
        player_location = slide_in(player_location,350,6)
        player_location[1] = 255
        screen.blit(get_image(image_src+'title.png'),(88,20))
        screen.blit(get_image(image_src+'text.png'),(0,425))
        screen.blit(get_image(image_src+'credit_text.png'),(374,520))
        screen.blit(get_image(image_src+'instructions.png'),(540,175))
        #buttons
        play_button = screen.blit(get_image(image_src+'buttons/play.png'),(540,50))
    elif activity == 'playing' and not pause:
        #angle
        angle += 1
        #player
        player_location = slide_in(player_location,75,6)
        player_location,delay = move_player(player_location,delay)
        player_hitbox = pygame.Rect(player_location[0],player_location[1],100,50)
        #meteors
        if wave < len(wave_list)+1 and meteor_check[level-1] == 1 and transition_timer == 0:
            object_spawn_cooldown, meteor_list = spawn_object(object_spawn_cooldown,meteor_list)
        meteor_list, meteors_to_delete = move_object(meteor_list, meteors_to_delete)
        material = 'meteor'
        meteor_hitboxes = rotate_object(meteor_list,material,angle)
        meteor_list, meteors_to_delete, particles = object_collision(meteor_list,meteor_hitboxes,meteors_to_delete,particles,material)
        #crystals
        if wave < len(wave_list)+1 and transition_timer == 0:
            object_spawn_cooldown, crystal_list = spawn_object(object_spawn_cooldown,crystal_list)
        crystal_list, crystals_to_delete = move_object(crystal_list,crystals_to_delete)
        material = 'crystal'
        crystal_hitboxes = rotate_object(crystal_list,material,angle)
        crystal_list, crystals_to_delete, particles = object_collision(crystal_list,crystal_hitboxes,crystals_to_delete,particles,material)
        #enemies
        if level_enemy_types[level-1] == 'ufo':
            if level > 6:
                total_enemy_hp = 3
                total_lasers = 1
            else:
                total_enemy_hp = 1
                total_lasers = 1
        elif level_enemy_types[level-1] == 'mover':
            if level > 7 :
                total_enemy_hp = 5
                total_lasers = 1
            else:
                total_enemy_hp = 3
                total_lasers = 1
        elif level_enemy_types[level-1] == 'boss':
            if level == 6:
                total_enemy_hp = 80
            elif level == 10:
                total_enemy_hp = 150
            total_lasers = 5
        if transition_timer == 0:
            enemy_list, wave = spawn_enemies(enemy_list,wave_list,wave,total_enemy_hp, level_enemy_types[level-1])
        enemy_list = move_enemies(enemy_list)
        #enemies shoot lasers
        if enemy_shoot_cooldown > 0 and len(enemy_list) > 0 and transition_timer == 0:
            enemy_shoot_cooldown -= 1
        if enemy_shoot_cooldown < 1 and len(enemy_list) > 0:
            enemy_shot.play()
            enemies = random.randint(1,3)
            if enemies > len(enemy_list):
                enemies = len(enemy_list)
            old_choice = ''
            choice = ''
            for e in range(enemies):
                old_choice = choice
                while choice == old_choice:
                    choice = random.choice(enemy_list)
                enemy_laser_list = spawn_enemy_laser(enemy_laser_list,choice,total_lasers)
            enemy_shoot_cooldown = 180
            if level_enemy_types[level-1] == 'boss':
                enemy_shoot_cooldown = 50
            elif level_enemy_types[level-1] == 'mover' and level > 7:
                enemy_shoot_cooldown = 150
        enemy_laser_list = move_lasers(enemy_laser_list,'enemy')
        enemy_laser_list, enemy_list, particles = laser_collision(enemy_laser_list, enemy_list, player_hitbox, level_enemy_types[level-1], 'enemy', particles)
        #player shoot lasers
        if score > (total_player_shots*1000)-1:
            if total_player_shots < 3:
                total_player_shots += 1
        pressed = pygame.key.get_pressed()
        if shoot_cooldown < 1:
            if pressed[pygame.K_SPACE]:
                player_shot.play()
                laser_list = spawn_laser(laser_list,player_location)
                shoot_cooldown = 20
        else:
            shoot_cooldown -= 1
            if total_player_shots > 1:
                if shoot_cooldown == 15:
                    player_shot.play()
                    laser_list = spawn_laser(laser_list,(player_location[0],player_location[1]+20))
                elif shoot_cooldown == 10 and total_player_shots > 2:
                    player_shot.play()
                    laser_list = spawn_laser(laser_list,(player_location[0],player_location[1]-20))
        laser_list = move_lasers(laser_list,'player')
        laser_list, enemy_list, particles = laser_collision(laser_list, enemy_list, player_hitbox, level_enemy_types[level-1], 'player', particles)
    if activity == 'playing':
        if pause:
            meteor_hitboxes = rotate_object(meteor_list,material,angle)
            crystal_hitboxes = rotate_object(crystal_list,material,angle)
        #render lasers
        for l in range(len(laser_list)):
            screen.blit(get_image(image_src+'player_laser.png'),laser_list[l])
        #render enemy lasers
        for l in range(len(enemy_laser_list)):
            screen.blit(get_image(image_src+'enemy_laser.png'),enemy_laser_list[l])
        #render enemies
        for e in range(len(enemy_list)):
            enemy_data = enemy_list[e]
            enemy = screen.blit(get_image(image_src+'enemies/'+level_enemy_types[level-1]+'.png'),(enemy_data[0],enemy_data[1]))
            pygame.draw.rect(screen,(2, 235, 215),pygame.Rect(enemy_data[0],enemy_data[1]-15,(enemy[2]/total_enemy_hp)*enemy_data[2],8))
            pygame.draw.rect(screen,(255,255,255),pygame.Rect(enemy_data[0],enemy_data[1]-15,enemy[2],8),1)
        #enemy_cooldown
        if len(enemy_list) < 1 and enemy_cooldown == 0: #it is important that this if statement remains before the next one or else there will be errors in the algorithm
            enemy_cooldown = 100
            enemy_shoot_cooldown = 180
        if enemy_cooldown > 0:
            enemy_cooldown -= 1
        #top bar
        screen.blit(get_image(image_src+'top_bar.png'),(0,0))
        for l in range(lives):
            screen.blit(get_image(image_src+'life.png'),(130+l*40,25))
        render_number(level,530,15)
        render_number(score,820,15)

        #next level check
        if wave > len(wave_list) and len(meteor_list) < 1 and len(crystal_list) < 1:
            if level < total_levels:
                level +=1
                if level > 9:
                    lives = addlife(lives, 3)
                elif level > 5:
                    lives = addlife(lives, 2)
                else:
                    lives = addlife(lives, 1)
                wave = 0
                transition = str(level)
                transitionY = 0
                transition_timer = 1
                player_location[0] = -100
                meteor_list = []
                meteors_to_delete = []
                object_spawn_cooldown = 120
                enemy_list = []
                enemy_cooldown = 100
                enemy_shoot_cooldown = 180
                enemy_laser_list = []
                wave = 0
                shoot_cooldown = 0
                pause = False
                wave_list = divide_in_waves(level_total_enemies[level-1],level_total_waves[level-1])
            else:
                level += 1
                activity = 'menu'
                transition = 'win'
                transitionY = 0
                transition_timer = 120
                won = True


    #player rendering
    if won:
        skin = '_racer'
    else:
        skin = ''
    player = get_image(image_src+'player'+skin+'.png')
    screen.blit(player, (player_location[0],player_location[1]))
    #render fire
    delay = delay*0.9
    draw_fire(player_location,4,delay)
    #particles
    particles = draw_particles(particles)
    #pause
    if pause:
        screen.blit(get_image(image_src+'pause.png'),(0,0))

    #transitions
    if transition != '':
        screen.blit(get_image(image_src+'transitions/'+transition+'.png'),(0,transitionY))
        if transition_timer == 0:
            transitionY += 10
        if transitionY > 560:
            transition = ''

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                transition_timer = 0
            if event.key == pygame.K_p and activity == 'playing':
                button_click.play()
                pause = not pause
            if event.key == pygame.K_m and pause:
                button_click.play()
                activity = 'menu'
                transition = 'menu'
                transitionY = 0
                transition_timer = 60
                pause = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            x, y = event.pos
            if activity == 'menu':
                if play_button.collidepoint(x, y):
                    button_click.play()
                    pause = False
                    activity = 'playing'
                    score = 0
                    level = 1
                    lives = 6
                    transition = str(level)
                    transitionY = 0
                    transition_timer = 1
                    angle = 0
                    player_location[0] = -100
                    delay = 0
                    meteor_list = []
                    meteors_to_delete = []
                    object_spawn_cooldown = 120
                    wave_list = divide_in_waves(level_total_enemies[level-1],level_total_waves[level-1])
                    enemy_list = []
                    enemy_cooldown = 100
                    enemy_shoot_cooldown = 180
                    enemy_laser_list = []
                    wave = 0
                    shoot_cooldown = 0
                    total_player_shots = 1
                    pause = False


    pygame.display.flip()
    clock.tick(60)

pygame.quit()
