#include <stdlib.h>
#include <string.h>

#include "sixel.h"
#include "sixel_hls.h"

#define SIXEL_RGB(r, g, b) ((r) + ((g) << 8) +  ((b) << 16))
#define SIXEL_PALVAL(n,a,m) (((n) * (a) + ((m) / 2)) / (m))
#define SIXEL_XRGB(r,g,b) SIXEL_RGB(SIXEL_PALVAL(r, 255, 100), SIXEL_PALVAL(g, 255, 100), SIXEL_PALVAL(b, 255, 100))

static sixel_color_t const sixel_default_color_table[] = {
	SIXEL_XRGB( 0,  0,  0),
	SIXEL_XRGB(20, 20, 80),
	SIXEL_XRGB(80, 13, 13),
	SIXEL_XRGB(20, 80, 20),
	SIXEL_XRGB(80, 20, 80),
	SIXEL_XRGB(20, 80, 80),
	SIXEL_XRGB(80, 80, 20),
	SIXEL_XRGB(53, 53, 53),
	SIXEL_XRGB(26, 26, 26),
	SIXEL_XRGB(33, 33, 60),
	SIXEL_XRGB(60, 26, 26),
	SIXEL_XRGB(33, 60, 33),
	SIXEL_XRGB(60, 33, 60),
	SIXEL_XRGB(33, 60, 60),
	SIXEL_XRGB(60, 60, 33),
	SIXEL_XRGB(80, 80, 80),
};

static int
set_default_color(sixel_image_t *image)
{
	int i;
	int n;
	int r;
	int g;
	int b;

	for (n = 1; n < 17; n++) {
		image->palette[n] = sixel_default_color_table[n - 1];
	}

	for (r = 0; r < 6; r++) {
		for (g = 0; g < 6; g++) {
			for (b = 0; b < 6; b++) {
				image->palette[n++] = SIXEL_RGB(r * 51, g * 51, b * 51);
			}
		}
	}

	for (i = 0; i < 24; i++) {
		image->palette[n++] = SIXEL_RGB(i * 11, i * 11, i * 11);
	}

	for (; n < DECSIXEL_PALETTE_MAX; n++) {
		image->palette[n] = SIXEL_RGB(255, 255, 255);
	}

	return (0);
}

static int
sixel_image_init(
    sixel_image_t    *image,
    int              width,
    int              height,
    int              fgcolor,
    int              bgcolor,
    int              use_private_register)
{
	int status = (-1);
	size_t size;

	size = (size_t)(width * height) * sizeof(sixel_color_no_t);
	image->width = width;
	image->height = height;
	image->data = (sixel_color_no_t *)malloc(size);
	image->ncolors = 2;
	image->use_private_register = use_private_register;

	if (image->data == NULL) {
		status = (-1);
		goto end;
	}
	memset(image->data, 0, size);

	image->palette[0] = bgcolor;

	if (image->use_private_register)
		image->palette[1] = fgcolor;

	image->palette_modified = 0;

	status = (0);

end:
	return status;
}


static int
image_buffer_resize(
    sixel_image_t   *image,
    int              width,
    int              height)
{
	int status = (-1);
	size_t size;
	sixel_color_no_t *alt_buffer;
	int n;
	int min_height;

	size = (size_t)(width * height) * sizeof(sixel_color_no_t);
	alt_buffer = (sixel_color_no_t *)malloc(size);
	if (alt_buffer == NULL) {
		free(image->data);
		image->data = NULL;
		status = (-1);
		goto end;
	}

	min_height = height > image->height ? image->height: height;
	if (width > image->width) {
		for (n = 0; n < min_height; ++n) {
			memcpy(alt_buffer + width * n,
			       image->data + image->width * n,
			       (size_t)image->width * sizeof(sixel_color_no_t));
			memset(alt_buffer + width * n + image->width,
			       0,
			       (size_t)(width - image->width) * sizeof(sixel_color_no_t));
		}
	} else {
		for (n = 0; n < min_height; ++n) {
			memcpy(alt_buffer + width * n,
			       image->data + image->width * n,
			       (size_t)width * sizeof(sixel_color_no_t));
		}
	}

	if (height > image->height) {
		memset(alt_buffer + width * image->height,
		       0,
		       (size_t)(width * (height - image->height)) * sizeof(sixel_color_no_t));
	}

	free(image->data);

	image->data = alt_buffer;
	image->width = width;
	image->height = height;

	status = (0);

end:
	return status;
}

static void
sixel_image_deinit(sixel_image_t *image)
{
	free(image->data);
	image->data = NULL;
}

int
sixel_parser_init(sixel_state_t *st,
                  sixel_color_t fgcolor, sixel_color_t bgcolor,
                  unsigned char use_private_register,
                  int cell_width, int cell_height)
{
	int status = (-1);

	st->state = PS_DECSIXEL;
	st->pos_x = 0;
	st->pos_y = 0;
	st->max_x = 0;
	st->max_y = 0;
	st->attributed_pan = 2;
	st->attributed_pad = 1;
	st->attributed_ph = 0;
	st->attributed_pv = 0;
	st->repeat_count = 1;
	st->color_index = 16;
	st->grid_width = cell_width;
	st->grid_height = cell_height;
	st->nparams = 0;
	st->param = 0;

	status = sixel_image_init(&st->image, 1, 1, fgcolor, bgcolor, use_private_register);

	return status;
}

int
sixel_parser_set_default_color(sixel_state_t *st)
{
	return set_default_color(&st->image);
}

int
sixel_parser_finalize(sixel_state_t *st, unsigned char *pixels)
{
	int status = (-1);
	int sx;
	int sy;
	sixel_image_t *image = &st->image;
	int x, y;
	sixel_color_no_t *src;
	unsigned char *dst;
	int color;

	if (++st->max_x < st->attributed_ph)
		st->max_x = st->attributed_ph;

	if (++st->max_y < st->attributed_pv)
		st->max_y = st->attributed_pv;

	sx = (st->max_x + st->grid_width - 1) / st->grid_width * st->grid_width;
	sy = (st->max_y + st->grid_height - 1) / st->grid_height * st->grid_height;

	if (image->width > sx || image->height > sy) {
		status = image_buffer_resize(image, sx, sy);
		if (status < 0)
			goto end;
	}

	if (image->use_private_register && image->ncolors > 2 && !image->palette_modified) {
		status = set_default_color(image);
		if (status < 0)
			goto end;
	}

	src = st->image.data;
	dst = pixels;
	for (y = 0; y < st->image.height; ++y) {
		for (x = 0; x < st->image.width; ++x) {
			color = st->image.palette[*src++];
			*dst++ = color >> 16 & 0xff;
			*dst++ = color >> 8 & 0xff;
			*dst++ = color >> 0 & 0xff;
			dst++;
		}
		for (; x < st->image.width; ++x) {
			color = st->image.palette[0];
			*dst++ = color >> 16 & 0xff;
			*dst++ = color >> 8 & 0xff;
			*dst++ = color >> 0 & 0xff;
			dst++;
		}
	}
	for (; y < st->image.height; ++y) {
		for (x = 0; x < st->image.width; ++x) {
			color = st->image.palette[0];
			*dst++ = color >> 16 & 0xff;
			*dst++ = color >> 8 & 0xff;
			*dst++ = color >> 0 & 0xff;
			dst++;
		}
	}

	status = (0);

end:
	return status;
}

int
sixel_parser_parse(sixel_state_t *st, unsigned char *p, size_t len)
{
	int status = (-1);
	int n;
	int i;
	int x;
	int y;
	int bits;
	int sixel_vertical_mask;
	int sx;
	int sy;
	int c;
	int pos;
	unsigned char *p0 = p;
	sixel_image_t *image = &st->image;

	if (! image->data)
		goto end;

	while (p < p0 + len) {
		switch (st->state) {
		case PS_ESC:
			goto end;

		case PS_DECSIXEL:
			switch (*p) {
			case '\x1b':
				st->state = PS_ESC;
				p++;
				break;
			case '"':
				st->param = 0;
				st->nparams = 0;
				st->state = PS_DECGRA;
				p++;
				break;
			case '!':
				st->param = 0;
				st->nparams = 0;
				st->state = PS_DECGRI;
				p++;
				break;
			case '#':
				st->param = 0;
				st->nparams = 0;
				st->state = PS_DECGCI;
				p++;
				break;
			case '$':
				st->pos_x = 0;
				p++;
				break;
			case '-':
				st->pos_x = 0;
				if (st->pos_y < DECSIXEL_HEIGHT_MAX - 5 - 6)
					st->pos_y += 6;
				else
					st->pos_y = DECSIXEL_HEIGHT_MAX + 1;
				p++;
				break;
			default:
				if (*p >= '?' && *p <= '~') {
					if ((image->width < (st->pos_x + st->repeat_count) || image->height < (st->pos_y + 6))
					        && image->width < DECSIXEL_WIDTH_MAX && image->height < DECSIXEL_HEIGHT_MAX) {
						sx = image->width * 2;
						sy = image->height * 2;
						while (sx < (st->pos_x + st->repeat_count) || sy < (st->pos_y + 6)) {
							sx *= 2;
							sy *= 2;
						}

						if (sx > DECSIXEL_WIDTH_MAX)
							sx = DECSIXEL_WIDTH_MAX;
						if (sy > DECSIXEL_HEIGHT_MAX)
							sy = DECSIXEL_HEIGHT_MAX;

						status = image_buffer_resize(image, sx, sy);
						if (status < 0)
							goto end;
					}

					if (st->color_index > image->ncolors)
						image->ncolors = st->color_index;

					if (st->pos_x + st->repeat_count > image->width)
						st->repeat_count = image->width - st->pos_x;

					if (st->repeat_count > 0 && st->pos_y - 5 < image->height) {
						bits = *p - '?';
						if (bits != 0) {
							sixel_vertical_mask = 0x01;
							if (st->repeat_count <= 1) {
								for (i = 0; i < 6; i++) {
									if ((bits & sixel_vertical_mask) != 0) {
										pos = image->width * (st->pos_y + i) + st->pos_x;
										image->data[pos] = st->color_index;
										if (st->max_x < st->pos_x)
											st->max_x = st->pos_x;
										if (st->max_y < (st->pos_y + i))
											st->max_y = st->pos_y + i;
									}
									sixel_vertical_mask <<= 1;
								}
							} else {
								for (i = 0; i < 6; i++) {
									if ((bits & sixel_vertical_mask) != 0) {
										c = sixel_vertical_mask << 1;
										for (n = 1; (i + n) < 6; n++) {
											if ((bits & c) == 0)
												break;
											c <<= 1;
										}
										for (y = st->pos_y + i; y < st->pos_y + i + n; ++y) {
											for (x = st->pos_x; x < st->pos_x + st->repeat_count; ++x)
												image->data[image->width * y + x] = st->color_index;
										}
										if (st->max_x < (st->pos_x + st->repeat_count - 1))
											st->max_x = st->pos_x + st->repeat_count - 1;
										if (st->max_y < (st->pos_y + i + n - 1))
											st->max_y = st->pos_y + i + n - 1;
										i += (n - 1);
										sixel_vertical_mask <<= (n - 1);
									}
									sixel_vertical_mask <<= 1;
								}
							}
						}
					}
					if (st->repeat_count > 0)
						st->pos_x += st->repeat_count;
					st->repeat_count = 1;
				}
				p++;
				break;
			}
			break;

		case PS_DECGRA:
			switch (*p) {
			case '\x1b':
				st->state = PS_ESC;
				p++;
				break;
			case '0':
			case '1':
			case '2':
			case '3':
			case '4':
			case '5':
			case '6':
			case '7':
			case '8':
			case '9':
				st->param = st->param * 10 + *p - '0';
				if (st->param > DECSIXEL_PARAMVALUE_MAX)
					st->param = DECSIXEL_PARAMVALUE_MAX;
				p++;
				break;
			case ';':
				if (st->nparams < DECSIXEL_PARAMS_MAX)
					st->params[st->nparams++] = st->param;
				st->param = 0;
				p++;
				break;
			default:
				if (st->nparams < DECSIXEL_PARAMS_MAX)
					st->params[st->nparams++] = st->param;
				if (st->nparams > 0)
					st->attributed_pad = st->params[0];
				if (st->nparams > 1)
					st->attributed_pan = st->params[1];
				if (st->nparams > 2 && st->params[2] > 0)
					st->attributed_ph = st->params[2];
				if (st->nparams > 3 && st->params[3] > 0)
					st->attributed_pv = st->params[3];

				if (st->attributed_pan <= 0)
					st->attributed_pan = 1;
				if (st->attributed_pad <= 0)
					st->attributed_pad = 1;

				if (image->width < st->attributed_ph ||
				        image->height < st->attributed_pv) {
					sx = st->attributed_ph;
					if (image->width > st->attributed_ph)
						sx = image->width;

					sy = st->attributed_pv;
					if (image->height > st->attributed_pv)
						sy = image->height;

					sx = (sx + st->grid_width - 1) / st->grid_width * st->grid_width;
					sy = (sy + st->grid_height - 1) / st->grid_height * st->grid_height;

					if (sx > DECSIXEL_WIDTH_MAX)
						sx = DECSIXEL_WIDTH_MAX;
					if (sy > DECSIXEL_HEIGHT_MAX)
						sy = DECSIXEL_HEIGHT_MAX;

					status = image_buffer_resize(image, sx, sy);
					if (status < 0)
						goto end;
				}
				st->state = PS_DECSIXEL;
				st->param = 0;
				st->nparams = 0;
			}
			break;

		case PS_DECGRI:
			switch (*p) {
			case '\x1b':
				st->state = PS_ESC;
				p++;
				break;
			case '0':
			case '1':
			case '2':
			case '3':
			case '4':
			case '5':
			case '6':
			case '7':
			case '8':
			case '9':
				st->param = st->param * 10 + *p - '0';
				if (st->param > DECSIXEL_PARAMVALUE_MAX)
					st->param = DECSIXEL_PARAMVALUE_MAX;
				p++;
				break;
			default:
				st->repeat_count = st->param;
				if (st->repeat_count == 0)
					st->repeat_count = 1;
				st->state = PS_DECSIXEL;
				st->param = 0;
				st->nparams = 0;
				break;
			}
			break;

		case PS_DECGCI:
			switch (*p) {
			case '\x1b':
				st->state = PS_ESC;
				p++;
				break;
			case '0':
			case '1':
			case '2':
			case '3':
			case '4':
			case '5':
			case '6':
			case '7':
			case '8':
			case '9':
				st->param = st->param * 10 + *p - '0';
				if (st->param > DECSIXEL_PARAMVALUE_MAX)
					st->param = DECSIXEL_PARAMVALUE_MAX;
				p++;
				break;
			case ';':
				if (st->nparams < DECSIXEL_PARAMS_MAX)
					st->params[st->nparams++] = st->param;
				st->param = 0;
				p++;
				break;
			default:
				st->state = PS_DECSIXEL;
				if (st->nparams < DECSIXEL_PARAMS_MAX)
					st->params[st->nparams++] = st->param;
				st->param = 0;

				if (st->nparams > 0) {
					st->color_index = 1 + st->params[0];
					if (st->color_index < 0)
						st->color_index = 0;
					else if (st->color_index >= DECSIXEL_PALETTE_MAX)
						st->color_index = DECSIXEL_PALETTE_MAX - 1;
				}

				if (st->nparams > 4) {
					st->image.palette_modified = 1;
					if (st->params[1] == 1) {
						if (st->params[2] > 360)
							st->params[2] = 360;
						if (st->params[3] > 100)
							st->params[3] = 100;
						if (st->params[4] > 100)
							st->params[4] = 100;
						image->palette[st->color_index]
						    = hls_to_rgb(st->params[2], st->params[3], st->params[4]);
					} else if (st->params[1] == 2) {
						if (st->params[2] > 100)
							st->params[2] = 100;
						if (st->params[3] > 100)
							st->params[3] = 100;
						if (st->params[4] > 100)
							st->params[4] = 100;
						image->palette[st->color_index]
						    = SIXEL_XRGB(st->params[2], st->params[3], st->params[4]);
					}
				}
				break;
			}
			break;
		default:
			break;
		}
	}

	status = (0);

end:
	return status;
}

void
sixel_parser_deinit(sixel_state_t *st)
{
	if (st)
		sixel_image_deinit(&st->image);
}
