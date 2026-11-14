import sys
from PIL import Image
files = sys.argv[2:]; out = sys.argv[1]
w, h = 960, 540
cols = 2; rows = (len(files) + 1) // 2
sheet = Image.new('RGB', (w * cols, h * rows), 'black')
for i, f in enumerate(files):
    sheet.paste(Image.open(f).convert('RGB').resize((w, h)), ((i % cols) * w, (i // cols) * h))
sheet.save(out, quality=88)
