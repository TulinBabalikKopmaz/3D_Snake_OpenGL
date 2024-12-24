import sys
import random
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from PIL import Image  # PIL kütüphanesini ekledik

# Global değişkenler
window_width, window_height = 1000, 1000   # Oyun penceresinin genişliğini ve yüksekliğini (piksel cinsinden) belirtir.
map_size = 20                              # Oyun alanının (haritasının) boyutunu belirtir. 
cell_size = 1                              # Her bir hücrenin boyutunu belirtir.
snake = [(5, 5)]                           # Yılanın pozisyonlarını (hücrelerini) tutan bir listedir. Yılanın her bir hücresi (x, y) koordinat çifti olarak temsil edilir. Başlangıçta [(5, 5)] olarak ayarlanmıştır.
snake_dir = (1, 0)                         # Yılanın hareket yönünü belirtir. (Başlangıçta sağa doğtu hareket)
game_over = False                          # Oyunun bitip bitmediğini belirten bir bayraktır
angle = -20                                # Yılanın gezindiği yüzeyin açısını ayarlamak için
speed = 130                                # Yılanın hızını ayarlamak için (mili saniye olarak)
button_pos = (-0.32, -0.5, 0.4, -0.3)      # "RESTART" butonunun pozisyonunu belirtir. (x1, y1, x2, y2)
main_window = None                         # Ana oyun penceresinin tanımlandığı değişkendir.
game_over_window = None                    # Game Over penceresinin tanımlandığı değişkendir.
score =0                                   # Oyuncunun skorunu tutan değişken  


# Elmaların pozisyonları (random başlangıç pozisyonları atanır)(0 ile 19 arasında sayı üretir. Çünkü map_size =20 sınır kenarları ayırır)
red_apple = (random.randint(0, map_size-1), random.randint(0, map_size-1))
bomb_apples = [(random.randint(0, map_size-1), random.randint(0, map_size-1)) for _ in range(4)]
diamond_apple = (random.randint(0, map_size-1), random.randint(0, map_size-1))
stone_apple = (random.randint(0, map_size-1), random.randint(0, map_size-1))
gold_apple = (random.randint(0, map_size-1), random.randint(0, map_size-1))

# Elmaların texture (Doku) değişkenleri
snake_tail_texture=None
snake_head_texture=None
red_texture = None
bomb_texture = None
diamond_texture = None
stone_texture = None
gold_texture = None

# Elmaların zamanlayıcıları, mili saniye olarak oyunda kalma süreleri
diamond_apple_timeout = 6000 
stone_apple_timeout = 6000
bomb_apple_timeout= 10000

# PNG dosyasını texture(Doku) olarak yükle
"""
    Bu fonksiyon, belirtilen dosya adını kullanarak bir görüntüyü yükler, 
    ters çevirir, byte dizisine çevirir ve OpenGL kullanarak bir doku olarak ayarlar. 
    Bu işlemler, grafik uygulamalarında veya oyunlarda 2D dokuların kullanılabilmesi için gereklidir.
""" 
def load_texture(filename):
    try:
        image = Image.open(filename)                            # Pillow kütüphanesi kullanılarak görüntü dosyasını açar.
        flipped_image = image.transpose(Image.FLIP_TOP_BOTTOM)  # Görüntüyü yatay eksende ters çevirir. OpenGL, görüntülerin köşe koordinatlarını farklı yorumlayabildiği için bu işlem gereklidir.
        ix = flipped_image.size[0]                              # Görüntünün genişliğini (ix) alır
        iy = flipped_image.size[1]                              # Görüntünün yüksekliğini (iy) alır
        image = flipped_image.tobytes("raw", "RGB")             # Görüntüyü byte dizisine çevirir.
        glClearColor(0.0, 0.0, 0.0, 0.0)	                    # Arka plan rengini belirler (Siyah)

        texture_id = glGenTextures(1)                           # Yeni bir doku kimliği (ID) oluşturur.
        glBindTexture(GL_TEXTURE_2D, texture_id)                # Bu kimliği etkin hale getirir
        #Doku Parametrelerini ayarlar
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)                        # Dokunun yatay (S) eksenlerde nasıl sarılacağını belirler. GL_REPEAT, dokunun tekrar etmesini sağlar.
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)                        # Dokunun dikey (T) eksenlerde nasıl sarılacağını belirler
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)                    # Dokunun büyümesi için filtre, GL_LINEAR değeri, doğrusal interpolasyon kullanarak daha pürüzsüz görüntüler sağlar.
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)                    # Dokunun küçülmesi için filtre
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, ix, iy, 0, GL_RGB, GL_UNSIGNED_BYTE, image)  # glTexImage2D fonksiyonu, doku verilerini OpenGL'e yükler.
        glEnable(GL_TEXTURE_2D)                                                             # 2D doku özelliğini etkinleştirir.
        return texture_id
    except IOError as e:
        print(f"Error loading texture: {e}")
        return -1

# Oyunda yer alan herşeyin doku kaplamasını yapan kısım. load_texture fonksiyonunu kullanmıştır.
def load_textures():
    global red_texture, bomb_texture, diamond_texture, stone_texture, gold_texture,snake_head_texture,snake_tail_texture
    red_texture = load_texture("apple.png")
    bomb_texture = load_texture("bomb.jpg")
    diamond_texture = load_texture("diamond_apple.png")
    stone_texture = load_texture("stone_apple.png")
    gold_texture = load_texture("gold_apple.jpg")
    snake_head_texture = load_texture("snake1.jpeg")
    snake_tail_texture = load_texture("snake.JPG")

    # Eğer texture'lar yüklenemediyse hata mesajı yazdır
    if red_texture == -1 or bomb_texture == -1 or diamond_texture == -1 or stone_texture == -1 or gold_texture == -1:
        print("Texture loading failed. Check if the files exist and are in the correct format.")
  
# Ses efektlerinin yüklendiği kısım pygame kütüphanesi kullanılmıştır.        
def load_sounds():
    global eat_sound, bomb_sound, stone_sound,game_over_sound
    pygame.mixer.init()
    eat_sound = pygame.mixer.Sound("eat.wav")
    bomb_sound = pygame.mixer.Sound("bomb_sound.wav")
    stone_sound = pygame.mixer.Sound("stone_sound.wav")
    game_over_sound=pygame.mixer.Sound("game_over_sound.wav")
    


# OpenGL'i başlatan fonksiyon
def init():
    
    glEnable(GL_DEPTH_TEST)                                     # 3 boyutlu cisimlerdeki derinlik algısını aktifleştirir
    glEnable(GL_LIGHTING)                                       # Işıklandırmayı etkinleştir
    glEnable(GL_LIGHT0)                                         # Bir ışık kaynağı ekler
    glEnable(GL_COLOR_MATERIAL)                                 # Nesnelerin renklerini ışıklandırmaya göre ayarlar
    glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)           # Materyalin renk özelliklerini belirler.
    # GL_FRONT parametresi, sadece öndeki yüzeyler için renk özelliklerinin geçerli olacağını belirtir.
    # GL_AMBIENT_AND_DIFFUSE, ortam ve yayılmış (diffüz) ışık bileşenlerinin materyalin renginden etkileneceğini belirtir.
    glShadeModel(GL_SMOOTH)                                     # Gölgeleme modelini ayarlar.
    # GL_SMOOTH Bu model, kenarlar arasında renklerin yumuşak geçişini sağlar
    gluPerspective(55, window_width / window_height, 1, 100)    # Perspektif projeksiyon matrisini tanımlar.
    glTranslatef(-map_size / 2, -map_size / 2, -map_size * 1.09)# Model görüntüleme matrisini belirli bir vektör boyunca çevirir.
    # -map_size * 1.09 , z ekseninde çevirme miktarıdır. Bu, sahneyi gözlemciden belirli bir mesafeye yerleştirir, sahnenin tamamını görünür hale getirir.
    
# Oyun yüzeyinde yer alan ızgaralı kısımı çizer
"""
Bu fonksiyon, map_size değişkenine bağlı olarak belirli bir boyutta ızgara çizer. 
Bu ızgara, genellikle bir oyun veya 3D sahne için referans noktası olarak kullanılır. 
Izgaranın her çizgisi beyaz renkte çizilir ve zeminde (z = 0) yer alır.
"""
def draw_grid():
    glColor3f(1.0, 1.0, 1.0)         # Sonraki çizim işlemleri için renk ayarını yapar
    glBegin(GL_LINES)                # Çizim modunu başlatır.GL_LINES, iki nokta arasında düz çizgi çizer
    for x in range(map_size + 1):    # x eksenindeki dikey çizgileri çizmek için kullanılır.
        glVertex3f(x, 0, 0)          # Çizginin başlangıç noktasını belirler.
        glVertex3f(x, map_size, 0)   # Çizginin bitiş noktasını belirler.
    for y in range(map_size + 1):    # y eksenindeki dikey çizgileri çizmek için kullanılır.
        glVertex3f(0, y, 0)
        glVertex3f(map_size, y, 0)
    glEnd()

# Verilen pozisyonda, verilen dokuya sahip bir küp çizer. (harita 20x20 karelerden oluşuyor. her bir küpde 1 kareye sığıcak şekilde çizildi)
def draw_cube(position, texture_id):
    x, y = position
    glBindTexture(GL_TEXTURE_2D, texture_id)   # Kullanılacak dokuyu belirler

    half_depth = -0.5                          # Küpün yarı derinliği

    # Ön yüz
    glBegin(GL_QUADS)                          # Çizim modunu başlatır
    glTexCoord2f(0, 0)                         # Dokunun hangi bölümünün kullanılacağını belirler
    glVertex3f(x, y, -half_depth)              # Bir Köşenin koordinatlarını belirtir.
    glTexCoord2f(1, 0)
    glVertex3f(x + 1, y, -half_depth)          # +1 ler bir kareye sığsın diye yapıldı
    glTexCoord2f(1, 1)
    glVertex3f(x + 1, y + 1, -half_depth)
    glTexCoord2f(0, 1)
    glVertex3f(x, y + 1, -half_depth)
    glEnd()

    # Arka yüz
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0)
    glVertex3f(x, y, half_depth)
    glTexCoord2f(1, 0)
    glVertex3f(x + 1, y, half_depth)
    glTexCoord2f(1, 1)
    glVertex3f(x + 1, y + 1, half_depth)
    glTexCoord2f(0, 1)
    glVertex3f(x, y + 1, half_depth)
    glEnd()

    # Üst Yüz
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0)
    glVertex3f(x, y + 1, -half_depth)
    glTexCoord2f(1, 0)
    glVertex3f(x + 1, y + 1, -half_depth)
    glTexCoord2f(1, 1)
    glVertex3f(x + 1, y + 1, half_depth)
    glTexCoord2f(0, 1)
    glVertex3f(x, y + 1, half_depth)
    glEnd()

    # Alt Yüz
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0)
    glVertex3f(x, y, -half_depth)
    glTexCoord2f(1, 0)
    glVertex3f(x, y, half_depth)
    glTexCoord2f(1, 1)
    glVertex3f(x + 1, y, half_depth)
    glTexCoord2f(0, 1)
    glVertex3f(x + 1, y, -half_depth)
    glEnd()

    # Sağ yüz
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0)
    glVertex3f(x + 1, y, -half_depth)
    glTexCoord2f(1, 0)
    glVertex3f(x + 1, y, half_depth)
    glTexCoord2f(1, 1)
    glVertex3f(x + 1, y + 1, half_depth)
    glTexCoord2f(0, 1)
    glVertex3f(x + 1, y + 1, -half_depth)
    glEnd()

    # Sol Yüz
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0)
    glVertex3f(x, y, -half_depth)
    glTexCoord2f(1, 0)
    glVertex3f(x, y + 1, -half_depth)
    glTexCoord2f(1, 1)
    glVertex3f(x, y + 1, half_depth)
    glTexCoord2f(0, 1)
    glVertex3f(x, y, half_depth)
    glEnd()

# Yılanın akuyruğunu Çiz
def draw_snake_tail():
    glColor3f(0.0, 0.5, 0.0)                   # Yeşil renk
    for segment in snake[:-1]:                 # Yılanın son elemanı (yani başı) hariç her segment için döngü oluşturulur.
        draw_cube(segment, snake_tail_texture) # Her bir segment için draw_cube() fonksiyonu çağrılır. Bu, yılanın her bir parçasının çizilmesini sağlar. segment parametresi, çizilecek küpün konumunu belirtir ve snake_tail_texture ise kullanılacak olan dokuyu temsil eder.
        
# Yılanın başını Çiz
def draw_snake():
    glColor3f(1.0, 1.0, 1.0)                   # Beyaz renk
    draw_cube(snake[-1], snake_head_texture)   # Yılanın başını çizmek için draw_cube fonksiyonunu kullanır. snake[-1], yılanın son segmentini temsil eder, yani başını. snake_head_texture ise başın görüntüsünü temsil eden bir doku kimliğidir. 
    draw_snake_tail()                          # Kuyruk kısmını çizicek fonksiyonu çağır

# Elmaların çizimi
def draw_red_apple():
    glColor3f(1.0, 1.0, 1.0)                   # Beyaz renk
    glBindTexture(GL_TEXTURE_2D, red_texture)  # 2B dokunun kullanılacağı bir sonraki işlemin belirtildiği bir işlemdir. GL_TEXTURE_2D hedefi belirler ve red_texture ise kullanılacak olan dokunun kimliğidir.
    draw_cube(red_apple, red_texture)          # Verilen pozisyona göre (global değişkenlerde random olarak) ve dokuya göre küpü oluşturur.
    
def draw_bomb_apples():
    glColor3f(1.0, 1.0, 1.0)
    for bomb_apple in bomb_apples:
        glBindTexture(GL_TEXTURE_2D, bomb_texture)
        draw_cube(bomb_apple, bomb_texture)

def draw_diamond_apple():
    glColor3f(1.0, 1.0, 1.0)
    glBindTexture(GL_TEXTURE_2D, diamond_texture)
    draw_cube(diamond_apple, diamond_texture)

def draw_stone_apple():
    glColor3f(1.0, 1.0, 1.0)
    glBindTexture(GL_TEXTURE_2D, stone_texture)
    draw_cube(stone_apple, stone_texture)

def draw_gold_apple():
    glColor3f(1.0, 1.0, 1.0)
    glBindTexture(GL_TEXTURE_2D, gold_texture)
    draw_cube(gold_apple, gold_texture)

def setup_snake_lights():
    # Baş ışığını tanımla ve ayarla
    glEnable(GL_LIGHT1)
    glLightfv(GL_LIGHT1, GL_DIFFUSE, [4.0, 4.0, 4.0, 1.0])                 # Beyaz renk
    glLightfv(GL_LIGHT1, GL_POSITION, [snake[-1][0], snake[-1][1], 1, 1])  # Başın konumu

    # Kuyruk ışığını tanımla ve ayarla
    glEnable(GL_LIGHT2)
    glLightfv(GL_LIGHT2, GL_DIFFUSE, [3.0, 3.0, 3.0, 1.0])               # Beyaz renk
    glLightfv(GL_LIGHT2, GL_POSITION, [snake[0][0], snake[0][1], 1, 1])  # Kuyruğun konumu
    
# Oyun ekranını güncelle
def display():
    global angle
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # Renk ve derinlik tamponlarını temizler, bu da ekranı temizler ve yeni çizimler için hazır hale getirir.
    glPushMatrix()                # Mevcut modelleme matrisini yığına koyar, böylece sonraki dönüşümler geri alınabilir.
    glRotatef(angle, 9, 0, 0)     # angle değişkenine bağlı olarak sahneyi 9 derece çevirir.
    setup_snake_lights()          # Baş ve kuyruk ışıklarını ayarla
    draw_grid()                   # Izgara haritayı çiz
    draw_snake()                  # Yılanı çiz
    draw_red_apple()              # Kırmızı elmayı çiz
    draw_bomb_apples()            # TNT elmayı çiz
    draw_diamond_apple()          # Elmas elmasını çiz
    draw_stone_apple()            # Taş elmayı çiz
    draw_gold_apple()             # Altın elmayı çiz
    glPopMatrix()                 # En son push edilen modelleme matrisini yığından çıkarır, böylece önceki duruma döner.
    glutSwapBuffers()             # Çift tamponlamayı kullanarak, çizim tamamlandığında ön tampon ile arka tamponu değiştirir, böylece ekrana çizilenleri görünür kılar.
         

# Timer callback
def timer(value):
    global game_over
    if not game_over:
        move_snake()
        check_collision()
        update_apple_timers()
        glutPostRedisplay()
        glutTimerFunc(speed, timer, 0)

def update_apple_timers():
    global diamond_apple_timeout, stone_apple_timeout,bomb_apple_timeout
    diamond_apple_timeout -= speed
    stone_apple_timeout -= speed
    bomb_apple_timeout -=speed

    if diamond_apple_timeout <= 0:
        place_diamond_apple()                # Diamond applenın Konumunu günceller
        diamond_apple_timeout = 6000

    if stone_apple_timeout <= 0:
        place_stone_apple()                  # Stone applenın Konumunu günceller
        stone_apple_timeout = 6000
        
    if bomb_apple_timeout <= 0:
        place_bomb_apples()                  # Bomb applenın Konumunu günceller
        bomb_apple_timeout = 10000
        
# Çarpışma Kontrolleri
def check_collision():
    global game_over, speed,score
    head = snake[-1]                         # snake listesinin son elemanı, yani yılanın başının konumu, head değişkenine atanır.
    
    if  speed > 40 :                         # Yılanın hızı, oyunun başladığından beri yılanın uzunluğuna göre dinamik olarak ayarlanır. Eğer hız 40'tan büyükse, yani oyun başladığından beri yılanın uzunluğu 5'ten büyükse, hızı düşürmek için bir hesaplama yapılır.
        katsayi = (len(snake)-1) / 5         # Her 5 kare uzamada 10 ms hız düşücek başta hızı 130 ve minimum 40 ms kadar inebilir
        speed = 130 - int(katsayi)*10

    # Harita sınırlarının kontrolü ve yılanın kendisine çarpması durumu
    if not (0 <= head[0] < map_size and 0 <= head[1] < map_size) or head in snake[:-1]:    # Eğer yılanın başının x ve y koordinatları harita sınırları içinde değilse veya yılanın başı, yılanın kalan segmentlerinden herhangi birine çarpıyorsa
        game_over = True                                                                   # Oyun biter
        show_game_over_window()                                                            # Game over penceresini göster
        return

    if head in bomb_apples:                  # Eğer bomb apple olduğu konuma gelirse kafa
        bomb_sound.play()                    # Bomb apple çarptığında patlama sesi oynat
        game_over = True                     # Oyun biter
        show_game_over_window()              # Game over penceresini göster
        return

    if head == red_apple:                    # Eğer red apple olduğu konuma gelirse kafa
        eat_sound.play()                     # Yeme sesini oynat
        snake.append(snake[-1])              # snake adlı listenin sonuna listenin son elemanını ekliyor. Yani yılanın kuyruğu, yılanın başının mevcut pozisyonuna bir segment daha eklenerek uzatılıyor. 
        score  = score + 1                   # skoru 1 artırıyor
        place_red_apple()

    elif head == diamond_apple:             # Eğer diamond apple olduğu konuma gelirse kafa
        eat_sound.play()                    # Yeme sesini oynat
        snake.append(snake[-1])             # Yılanın boyu 3 uzuyor ve skorda 3 artıyor
        score  = score + 1
        snake.append(snake[-1])
        score  = score + 1
        snake.append(snake[-1])
        score  = score + 1
        place_diamond_apple()               # Konumunu günceller

    elif head == stone_apple:               # Eğer stone apple olduğu konuma gelirse kafa
        stone_sound.play()                  # Çarpma sesini oynat
        if len(snake) == 1:                 # Eğer yılanın uzunluğu 1 ise yani sadece kafası varsa ve taş yediyse oyun biter
            game_over = True                # Oyun biter
            show_game_over_window()         # Game over penceresini göster
            return
        else:                               # Eğer yılanın uzunluğu 1 den farklı ise yani kuyruğu da varsa ve taş yediğinde kuyruk 1 azalır
            snake.pop()                     # Listenin sonundaki öğeyi kaldırır ve kaldırılan öğeyi döndürür. Bu durumda, yılanın kuyruğundaki son segmenti kaldırır. 
            score  = score - 1              # skoru 1 azaltıyor
        place_stone_apple()                 # Konumunu günceller

    elif head == gold_apple:                # Eğer gold apple olduğu konuma gelirse kafa
        eat_sound.play()                    # Yeme sesi oynat
        snake.append(snake[-1])             # Yılanın boyu 3 uzuyor ve skorda 3 artıyor
        score  = score + 1
        snake.append(snake[-1])
        score  = score + 1
        place_gold_apple()                  # Konumunu günceller

def special_input(key, x, y):                     # Yılanı Kalvyedeki yön tuşlarını kullanarak kontrol etmek için
    global snake_dir
    if key == GLUT_KEY_UP and snake_dir != (0, -1):
        snake_dir = (0, 1)
    elif key == GLUT_KEY_DOWN and snake_dir != (0, 1):
        snake_dir = (0, -1)
    elif key == GLUT_KEY_LEFT and snake_dir != (1, 0):
        snake_dir = (-1, 0)
    elif key == GLUT_KEY_RIGHT and snake_dir != (-1, 0):
        snake_dir = (1, 0)

def keyboard(key, x, y):                          # Yılanı Kalvyedeki w a s d  tuşlarını kullanarak kontrol etmek için, ayrıca yüzey azısınıda z ve x tuşlarıyla kontrol etmek için
    global snake_dir, angle,speed
    if key == b'w' and snake_dir != (0, -1):
        snake_dir = (0, 1)
    elif key == b's' and snake_dir != (0, 1):
        snake_dir = (0, -1)
    elif key == b'a' and snake_dir != (1, 0):
        snake_dir = (-1, 0)
    elif key == b'd' and snake_dir != (-1, 0):
        snake_dir = (1, 0)
    elif key == b'z':
        angle = (angle + 5) % 360
    elif key == b'x':
        angle = (angle - 5) % 360
    elif key == b' ':
        speed = speed - 5
    elif key == b'n':
        speed = speed + 5


def move_snake():
    global snake, game_over
    new_head = (snake[-1][0] + snake_dir[0], snake[-1][1] + snake_dir[1])
    
    if new_head[0] >= map_size:
        new_head = (0, new_head[1])
    elif new_head[0] < 0:
        new_head = (map_size - 1, new_head[1])
    elif new_head[1] >= map_size:
        new_head = (new_head[0], 0)
    elif new_head[1] < 0:
        new_head = (new_head[0], map_size - 1)

    if new_head in snake or not (0 <= new_head[0] < map_size and 0 <= new_head[1] < map_size):
        game_over = True
        show_game_over_window()
        return

    snake.append(new_head)
    snake.pop(0)

def place_red_apple():                                                                            #  Kırmızı elmanın haritada rastgele bir yere yerleştirilmesinden sorumludur.
    global red_apple                                                                              # eski rasgele konumu
    while True:                                                                                   # Geçerli bir konum bulunana kadar sürekli olarak çalışır.
        new_red_apple = (random.randint(0, map_size - 1), random.randint(0, map_size - 1))        # yeni ras gele konum üretir, harita içinde
        # Önceki kırmızı elma pozisyonları ile kıyaslayın
        valid_position = True
        for apple in bomb_apples + [diamond_apple, stone_apple, gold_apple]:                      
            if abs(new_red_apple[0] - apple[0]) < 4 and abs(new_red_apple[1] - apple[1]) < 4:
                valid_position = False
                break
        # Bomba elmaları ile çakışmayı kontrol edin
        if new_red_apple in bomb_apples:
            valid_position = False
        # Yılan ile çakışmayı kontrol edin
        if new_red_apple in snake:
            valid_position = False
        # Eğer geçerli bir konum bulursak, kırmızı elmayı yerleştirin
        if valid_position:
            red_apple = new_red_apple
            break

def place_bomb_apples():
    global bomb_apples
    bomb_apples = []
    while len(bomb_apples) < 4:
        new_bomb_apple = (random.randint(0, map_size - 1), random.randint(0, map_size - 1))
        # Önceki bomba elma pozisyonları ile kıyaslayın
        valid_position = True
        for apple in bomb_apples:
            if abs(new_bomb_apple[0] - apple[0]) < 4 and abs(new_bomb_apple[1] - apple[1]) < 4:
                valid_position = False
                break
        # Kırmızı elma ile çakışmayı kontrol edin
        if new_bomb_apple == red_apple:
            valid_position = False
        # Yılan ile çakışmayı kontrol edin
        if new_bomb_apple in snake:
            valid_position = False
        # Eğer geçerli bir konum bulursak, bomba elmalar listesine ekleyin
        if valid_position:
            bomb_apples.append(new_bomb_apple)

def place_diamond_apple():
    global diamond_apple
    while True:
        new_diamond_apple = (random.randint(0, map_size - 1), random.randint(0, map_size - 1))
        # Önceki elma pozisyonları ile kıyaslayın
        valid_position = True
        for apple in bomb_apples + [red_apple, stone_apple, gold_apple]:
            if abs(new_diamond_apple[0] - apple[0]) < 4 and abs(new_diamond_apple[1] - apple[1]) < 4:
                valid_position = False
                break
        # Bomba elmaları ile çakışmayı kontrol edin
        if new_diamond_apple in bomb_apples:
            valid_position = False
        # Yılan ile çakışmayı kontrol edin
        if new_diamond_apple in snake:
            valid_position = False
        # Eğer geçerli bir konum bulursak, elmayı yerleştirin
        if valid_position:
            diamond_apple = new_diamond_apple
            break
        
def place_stone_apple():
    global stone_apple
    while True:
        new_stone_apple = (random.randint(0, map_size - 1), random.randint(0, map_size - 1))
        # Önceki elma pozisyonları ile kıyaslayın
        valid_position = True
        for apple in bomb_apples + [red_apple, diamond_apple, gold_apple]:
            if abs(new_stone_apple[0] - apple[0]) < 4 and abs(new_stone_apple[1] - apple[1]) < 4:
                valid_position = False
                break
        # Bomba elmaları ile çakışmayı kontrol edin
        if new_stone_apple in bomb_apples:
            valid_position = False
        # Yılan ile çakışmayı kontrol edin
        if new_stone_apple in snake:
            valid_position = False
        # Eğer geçerli bir konum bulursak, elmayı yerleştirin
        if valid_position:
            stone_apple = new_stone_apple
            break

def place_gold_apple():
    global gold_apple
    while True:
        new_gold_apple = (random.randint(0, map_size - 1), random.randint(0, map_size - 1))
        # Önceki elma pozisyonları ile kıyaslayın
        valid_position = True
        for apple in bomb_apples + [red_apple, diamond_apple, stone_apple]:
            if abs(new_gold_apple[0] - apple[0]) < 4 and abs(new_gold_apple[1] - apple[1]) < 4:
                valid_position = False
                break
        # Bomba elmaları ile çakışmayı kontrol edin
        if new_gold_apple in bomb_apples:
            valid_position = False
        # Yılan ile çakışmayı kontrol edin
        if new_gold_apple in snake:
            valid_position = False
        # Eğer geçerli bir konum bulursak, elmayı yerleştirin
        if valid_position:
            gold_apple = new_gold_apple
            break

def show_game_over_window():
    global game_over_window,speed
    speed = 130
    if game_over_window is not None:
        glutDestroyWindow(game_over_window)
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
    glutInitWindowSize(400, 300)
    game_over_window = glutCreateWindow(b'Game Over')
    glutDisplayFunc(display_game_over)
    game_over_sound.play()
    glutMouseFunc(mouse_click)
    glutMainLoop()
    
def draw_play_button_text():
    glColor3f(0, 0, 0)
    glRasterPos2f(-0.27, -0.45)
    for char in b"TEKRAR OYNA":
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, char)

def display_game_over():
    global score
    glClear(GL_COLOR_BUFFER_BIT)
    glColor3f(1, 1, 1)
    glRasterPos2f(-0.23, 0.2)
    for char in b"GAME OVER":
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, char)
        
    glColor3f(1, 1, 1)
    score_text = f"SCORE: {score}"
    glRasterPos2f(-0.15, 0.0)
    for char in score_text.encode():
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, char)
        
    glColor3f(1, 1, 1)
    score_text = f"TULIN BABALIK KOPMAZ"
    glRasterPos2f(-0.85, -0.7)
    for char in score_text.encode():
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_10, char)
        
    glColor3f(1, 1, 1)
    score_text = f"AYSENUR YORUR"
    glRasterPos2f(-0.85, -0.84)
    for char in score_text.encode():
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_10, char)
        
    glColor3f(1, 1, 1)
    glBegin(GL_QUADS)
    glVertex2f(button_pos[0], button_pos[1])
    glVertex2f(button_pos[2], button_pos[1])
    glVertex2f(button_pos[2], button_pos[3])
    glVertex2f(button_pos[0], button_pos[3])
    glEnd()
    
    draw_play_button_text()
    
    glFlush()

def mouse_click(button, state, x, y):
    global score
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        ogl_x = (x / 400.0) * 2 - 1
        ogl_y = -((y / 300.0) * 2 - 1)
        score = 0
        if button_pos[0] <= ogl_x <= button_pos[2] and button_pos[1] <= ogl_y <= button_pos[3]:
            restart_game()

def restart_game():
    global snake, snake_dir, game_over, red_apple, diamond_apple, stone_apple, gold_apple, main_window, game_over_window,score
    snake = [(5, 5)]
    snake_dir = (1, 0)
    game_over = False
    score=0
    red_apple = (random.randint(0, map_size-1), random.randint(0, map_size-1))
    place_bomb_apples()
    diamond_apple = (random.randint(0, map_size-1), random.randint(0, map_size-1))
    stone_apple = (random.randint(0, map_size-1), random.randint(0, map_size-1))
    gold_apple = (random.randint(0, map_size-1), random.randint(0, map_size-1))
    if main_window is not None:
        glutDestroyWindow(main_window)
    if game_over_window is not None:
        glutDestroyWindow(game_over_window)
    main()

def main():
    global main_window
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(window_width, window_height)
    main_window = glutCreateWindow(b'Snake Game 3D')
    load_textures()  # Texture'ları yükle
    load_sounds()    # Ses dosyalarını yükle
    init()
    glutDisplayFunc(display)
    glutTimerFunc(speed, timer, 0)
    glutSpecialFunc(special_input)
    glutKeyboardFunc(keyboard)
    
    glutMainLoop()

if __name__ == '__main__':
    main()

