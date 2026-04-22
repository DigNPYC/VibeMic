from PIL import Image, ImageDraw, ImageFont

# 创建 256x256 的大图标
width = 256
height = 256
color = '#00AA00'  # 绿色背景

image = Image.new('RGB', (width, height), color)
dc = ImageDraw.Draw(image)

# 绘制 V 字（按比例放大）
points = [
    (56, 56),   # 左上
    (128, 200), # V 字底部
    (200, 56),  # 右上
]
dc.line(points + [points[0]], fill='white', width=32)

# 保存 PNG 图标
image.save('icon.png', 'PNG')
print("图标已生成: icon.png (256x256)")

# 转换为 ICO 格式（Windows 可用）
image.save('icon.ico', format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
print("图标已生成: icon.ico")
