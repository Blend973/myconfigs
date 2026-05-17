float
clamp(float value, float lower, float upper) {
	return value < lower ? lower : (value > upper ? upper : value);
}

void
changealpha(const Arg *arg)
{
	alpha = clamp(arg->f ?  alpha + arg->f : alpha_def, 0.0, 1.0);
	xloadcols();
	redraw();
}


