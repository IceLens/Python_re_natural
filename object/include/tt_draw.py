import io
import os
import random
import turtle
import urllib.request

from PIL import Image

'''
这是一个彩蛋脚本
'''


# 随机的美
def tt_draw_random():
    turtle.penup()
    turtle.fd(-100)
    turtle.pendown()
    for i in range(100):
        turtle.pensize(random.randint(1, 5))
        turtle.fd(random.randint(10, 50))
        turtle.seth(random.randint(1, 360))
        turtle.speed(random.randint(1, 20))
        turtle.circle(random.randint(1, 360), random.randint(0, 40))

    turtle.done()


def tt_draw_polyhedral():
    turtle.color('red')
    turtle.width(2)
    for x in range(100):
        turtle.fd(2 * x)
        turtle.left(58)

    turtle.done()


def get_color(r, g, b, alpha=256):
    # 获取原图片的颜色信息
    rr = r / 255.0
    bb = b / 255.0
    gg = g / 255.0
    if rr > 1.0:
        rr = 1.0
    if bb > 1.0:
        bb = 1.0
    if gg > 1.0:
        gg = 1.0
    return rr, gg, bb


# 使用 turtle 库绘制图片
def tt_draw_picture(url, pixel_size=5, width_pixel=1.0, height_pixel=1.0):
    # 打开本地图片
    if os.access(url, os.R_OK):
        im = Image.open(url)
    # 打开网络图片
    else:
        image_bytes = urllib.request.urlopen(url).read()
        data_stream = io.BytesIO(image_bytes)
        im = Image.open(data_stream)
    # 图片大小及其调整
    width, height = im.size
    width, height = round(width * width_pixel), round(height * height_pixel)
    im = im.resize((width, height))
    # 居中图片绘制
    turtle.setup(100 + width * pixel_size, 100 + height * pixel_size, 10, 10)
    turtle.speed(60)
    turtle.penup()
    turtle.fd(-(width * pixel_size / 2))
    turtle.seth(90)
    turtle.fd(height * pixel_size / 2)
    turtle.seth(0)
    turtle.pensize(pixel_size)
    turtle.pendown()
    for i in range(height):
        for j in range(width):
            turtle.pencolor(get_color(*im.getpixel((j, i))))
            turtle.fd(pixel_size)
        turtle.penup()
        turtle.seth(-90)
        turtle.fd(pixel_size)
        turtle.seth(180)
        turtle.fd(pixel_size * width)
        turtle.seth(0)
        turtle.pendown()

    turtle.done()
