from PIL import Image, ImageDraw, ImageFont
import os


def draw_box(draw, xy, text, font, fill=(255, 255, 255), outline=(0, 0, 0)):
    x1, y1, x2, y2 = xy
    draw.rectangle(xy, fill=fill, outline=outline)
    # center text
    w, h = draw.textsize(text, font=font)
    tx = x1 + (x2 - x1 - w) / 2
    ty = y1 + (y2 - y1 - h) / 2
    draw.text((tx, ty), text, fill=(0, 0, 0), font=font)


def main():
    out_dir = os.path.join(os.path.dirname(__file__), '..', 'images')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.abspath(os.path.join(out_dir, 'library_diagram.png'))

    W, H = 1200, 800
    img = Image.new('RGB', (W, H), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype('DejaVuSans-Bold.ttf', 14)
        font_b = ImageFont.truetype('DejaVuSans-Bold.ttf', 16)
    except Exception:
        font = ImageFont.load_default()
        font_b = font

    # LibrarySystem box (top center)
    box_w, box_h = 360, 90
    box_x = (W - box_w) // 2
    box_y = 40
    draw_box(draw, (box_x, box_y, box_x + box_w, box_y + box_h), 'LibrarySystem\n- books: Dict[isbn, Book]\n- members: Dict[id, Member]\n- checkouts: Dict[id, Checkout]', font)

    # Member, Checkout, Book boxes
    left_x = 80
    mid_x = (W - 320) // 2
    right_x = W - 400
    y1 = 220
    draw_box(draw, (left_x, y1, left_x + 260, y1 + 120), 'Member (abstract)\n- member_id, name, email\n- checkouts[]', font)
    draw_box(draw, (mid_x, y1, mid_x + 320, y1 + 120), 'Checkout\n- checkout_id\n- member, book\n- due_date, return_date', font)
    draw_box(draw, (right_x, y1, right_x + 260, y1 + 120), 'Book\n- isbn, title, author\n- total_copies, available', font)

    # Member subclasses
    sub_y = y1 + 160
    sx = left_x
    draw_box(draw, (sx, sub_y, sx + 180, sub_y + 70), 'StudentMember', font)
    draw_box(draw, (sx + 200, sub_y, sx + 380, sub_y + 70), 'FacultyMember', font)
    draw_box(draw, (sx + 400, sub_y, sx + 580, sub_y + 70), 'PremiumMember', font)

    # SearchStrategy and Observers
    ss_x = 80
    ss_y = 420
    draw_box(draw, (ss_x, ss_y, ss_x + 260, ss_y + 70), 'SearchStrategy (I)\n+ search(books, q)', font)
    draw_box(draw, (ss_x + 300, ss_y, ss_x + 540, ss_y + 70), 'ISBNSearchStrategy\nTitleSearchStrategy', font)

    obs_x = right_x
    obs_y = 420
    draw_box(draw, (obs_x, obs_y, obs_x + 260, obs_y + 70), 'Observer (I)\n+ notify(msg)', font)
    draw_box(draw, (obs_x - 300, obs_y + 100, obs_x - 40, obs_y + 170), 'EmailNotifier\nSMSNotifier', font)

    # Lines: LibrarySystem -> Member/Book/Checkout
    lx = box_x + box_w // 2
    ly = box_y + box_h
    # to Member
    m_x = left_x + 130
    m_y = y1
    draw.line([(lx, ly), (m_x, m_y)], fill=(0, 0, 0), width=2)
    draw.text(((lx + m_x) / 2 - 30, (ly + m_y) / 2 - 20), 'manages', fill=(0, 0, 0), font=font)
    # to Checkout
    c_x = mid_x + 160
    c_y = y1
    draw.line([(lx, ly), (c_x, c_y)], fill=(0, 0, 0), width=2)
    # to Book
    b_x = right_x + 130
    b_y = y1
    draw.line([(lx, ly), (b_x, b_y)], fill=(0, 0, 0), width=2)

    # Member -> subclasses (IS-A)
    parent_bottom = y1 + 120
    draw.line([(left_x + 130, parent_bottom), (left_x + 130, sub_y)], fill=(0, 0, 0), width=2)
    draw.text((left_x + 140, (parent_bottom + sub_y) / 2 - 10), 'IS-A', fill=(0, 0, 0), font=font)

    # Member -> Checkout (HAS-A)
    draw.line([(left_x + 260, y1 + 40), (mid_x, y1 + 40)], fill=(0, 0, 0), width=2)
    draw.text(((left_x + 260 + mid_x) / 2 - 30, y1 + 25), 'HAS-A 0..*', fill=(0, 0, 0), font=font)

    # Checkout -> Book (HAS-A)
    draw.line([(mid_x + 320, y1 + 60), (right_x, y1 + 60)], fill=(0, 0, 0), width=2)
    draw.text(((mid_x + 320 + right_x) / 2 - 30, y1 + 45), 'HAS-A 1', fill=(0, 0, 0), font=font)

    img.save(out_path)
    print(f'Wrote diagram to: {out_path}')


if __name__ == '__main__':
    main()
