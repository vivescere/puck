import os
import sys
import math
import json
import random
import imghdr
import shutil
import urllib.request
import urllib.parse

from colorthief import ColorThief


def main():
	if len(sys.argv) != 2:
		print('usage: python puck.py [url|subreddit|filepath]')
		sys.exit(1)

	# To bypass user-agent retrictions
	opener = urllib.request.build_opener()
	opener.addheaders = [
		('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')
	]
	urllib.request.install_opener(opener)

	if os.path.exists('wallpaper.png'):
		os.remove('wallpaper.png')

	if os.path.exists(sys.argv[1]):
		try:
			if imghdr.what(sys.argv[1]) is None:
				print("error: The specified file is not an image.")
				sys.exit(1)
		except IsADirectoryError:
			print('error: You passed a folder, not an image.')
			sys.exit(1)

		shutil.copy(sys.argv[1], 'wallpaper.png')

	elif urllib.parse.urlparse(sys.argv[1]).scheme == "":
		print("=> Downloading..")
		success = False

		while not success:
			url = grab_random_picture(sys.argv[1])
			urllib.request.urlretrieve(url, 'wallpaper.png')

			if imghdr.what('wallpaper.png') is not None:
				success = True
			else:
				print('Not a valid image, trying again..')
	else:
		print("=> Downloading..")
		print(sys.argv[1])
		urllib.request.urlretrieve(sys.argv[1], 'wallpaper.png')

	print("=> Extracting primary color..")
	color_thief = ColorThief('wallpaper.png')
	# color = color_thief.get_color(quality=1)
	color = color_thief.get_color(quality=1)

	write_colors(color)

	print("=> Reloading i3")
	os.system('i3-msg reload >/dev/null 2>&1')

	print("=> Setting wallpaper")
	os.system("feh --bg-fill wallpaper.png >/dev/null 2>&1")


def grab_random_picture(subreddit):
	print("=> Grabbing random top wallpaper from /r/{}".format(sys.argv[1]))

	request = urllib.request.urlopen('https://www.reddit.com/r/{}/top/.json?count=100&limit=100&t=month'.format(subreddit))
	data = json.loads(request.read().decode(request.info().get_param('charset') or 'utf-8'))

	posts = data['data']['children']

	index = random.randint(0, len(posts))

	post = posts[index]['data']

	url = post['url']

	if urllib.parse.urlparse(post['url']).netloc == 'imgur.com' and (
		not url.endswith('.png') and not url.endswith('.jpg') and not url.endswith('.jpeg') and not url.endswith('.gif')
	):
		url = '{}.png'.format(url)

	print(post['title'])
	print(url)

	return url


def darken(percent, color):
	return tuple([max(min(int(x - percent * 255 / 100), 255), 0) for x in color])


def lighten(percent, color):
	return tuple([max(min(int(x + percent * 255 / 100), 255), 0) for x in color])


def write_colors(color):
	print('=> Writing color to config file..')

	config_path = os.path.expanduser('~/.config/i3/config')

	with open(config_path, 'r') as config:
		content = config.readlines()
		start, end, dmenu_index = None, None, None

		for index, line in enumerate(content):
			if line.strip() == "colors {":
				start = index + 1
			elif start and line.strip() == "}":
				end = index - 1
			elif line.strip() == '# dmenu':
				dmenu_index = index + 1

	del content[start:end]

	content.insert(start, '		background #%02x%02x%02x\n' % color)

	# If the image is too bright, switch the text color
	is_bright = math.sqrt(0.299 * color[0] ** 2 + 0.587 * color[1] ** 2 + 0.114 * color[2] ** 2) > 175
	print('is_bright?', is_bright)

	if dmenu_index is not None:
		del content[dmenu_index]

		content.insert(dmenu_index, "bindsym $mod+d exec dmenu_run -i -p \"$(hostname | sed 's/.*/\\u&/')\" -fn 'pixelsize=10' -nb '{}' -nf '#FFFFFF' -sf '#FFFFFF' -sb '{}' -sf '{}'\n".format(
			'#%02x%02x%02x' % color,
			'#FFFFFF',
			'#2b2b2b',
		))

	if is_bright:
		content.insert(start, '		statusline #2b2b2b\n')
		content.insert(start, '		separator #333333\n')

	content.insert(start, '		focused_workspace {} {} {}\n'.format(
		# Border,
		'#%02x%02x%02x' % darken(20, color),
		# Background
		'#%02x%02x%02x' % darken(20, color),
		# Font,
		'#2b2b2b' if is_bright else '#FFFFFF'
	))

	content.insert(start, '		inactive_workspace {} {} {}\n'.format(
		# Border,
		'#%02x%02x%02x' % lighten(5, color),
		# Background
		'#%02x%02x%02x' % darken(5, color),
		# Font,
		'#2b2b2b' if is_bright else '#FFFFFF'
	))

	with open(config_path, 'w') as config:
		config.write(''.join(content))


if __name__ == '__main__':
	main()
