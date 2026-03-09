from engine import Screen

s = Screen(9, 9, char_width=2)

s.draw_pixels(2, 4, ((0, 255, 0), (255, 128, 255), (0, 255, 0)))
s.render()
s.draw_empty()

s.draw_fx(lambda x: 2*x, 255)
s.render()
s.draw_empty()

s.draw_fy(lambda y: 2*y, 255)
s.render()
s.draw_empty()

s.draw_fxy(lambda x, y: (x-4)**2 + (y-4)**2 <= 2**2, 255)
s.render()
s.draw_empty()

s.add_text(3, 5, "tetris", "Tetris")
s.render()
s.remove_text("tetris")
s.draw_empty()

s.add_text(3, 6, "tetris", "Tetris!")
s.draw_fx(lambda x: 0, 255, layer=0)
s.draw_fx(lambda x: 8, 255, layer=0)
s.draw_fy(lambda y: 0, 255, layer=0)
s.draw_fy(lambda y: 8, 255, layer=0)
s.draw_empty()
s.draw_pixels(1, 1, ((128, 128, 0, 0, 128, 128, 128),))
s.draw_pixels(3, 3, ((255, 255, 0), (0, 255, 255), (0, 0, 0)))
s.render()
