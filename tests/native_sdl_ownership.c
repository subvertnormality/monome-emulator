/* Exercise actual norns display allocation/bind/paint/destruction. */
#include <pthread.h>
#include <sys/queue.h>
#include <stdio.h>
#include <cairo.h>
#include <lua.h>
#include <SDL2/SDL.h>
#include "hardware/io.h"
#include "hardware/screen/screens.h"
/* Unused registry entries only: no GPIO or input operations are exercised. */
input_ops_t enc_gpio_ops, key_gpio_ops, input_sdl_ops;
int main(void) {
  SDL_SetHint(SDL_HINT_NO_SIGNAL_HANDLERS,"1");
  for (int i=0;i<32;i++) {
    if (io_create(NULL,&screen_sdl_ops.io_ops) || io_setup_all()) return 2;
    matron_fb_t *fb=(matron_fb_t *)TAILQ_FIRST(&io_queue);
    cairo_surface_t *surface=cairo_image_surface_create(CAIRO_FORMAT_ARGB32,128,64);
    screen_sdl_ops.bind(fb,surface);screen_sdl_ops.paint(fb);
    cairo_surface_destroy(surface);
    io_destroy_all();
    if (!TAILQ_EMPTY(&io_queue)) return 3;
  }
  puts("32 SDL resource lifecycles completed");
  return 0;
}
