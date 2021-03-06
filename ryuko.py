#!/usr/bin/python2
""" Creates gifs from videos """
# Inspired by
# http://rarlindseysmash.com/posts/stupid-programmer-tricks-and-star-wars-gifs
# via https://news.ycombinator.com/item?id=6633490

import argparse
import glob
import os
import subprocess

CONVERT = os.path.join("bin", "convert")
OPTIMISE = os.path.join("bin", "gifsicle")
FFMPEG = os.path.join("bin", "ffmpeg")
LOGLEVEL = "info"


def run(cmd, environment=False):
    """ Runs a command passed as a list """
    if environment is False:
        return subprocess.call([str(c) for c in cmd])
    else:
        return subprocess.call([str(c) for c in cmd], env=environment)


def extract_subs(input_file, subfile):
    """ Extracts the subtitles to a .srt file"""
    run([FFMPEG, "-loglevel", LOGLEVEL, "-i", input_file, "-map", "0:s:0",
         subfile])


def offset_subs(subfile, offset):
    """ Offsets the subtitles by the specified ammount """
    run(["python", "subslider.py", subfile, "-%r" % int(offset)])


def get_frames(input_file, start, duration, fps=10, flip=False, sub=False, subfile="", x_scale=False, y_scale=False):
    """ Extracts the frames using FFMPEG """
    print "Extracting frames (call this 25%)"
    filters = []
    if x_scale is not False:
        filters += ["scale=%r:-1" % x_scale]
    if x_scale is not False and y_scale is not False:
        filters += ["scale=-1:%r" % y_scale]
    if x_scale is not False and y_scale is not False:
        filters[0] = ["scale=%r:%r" % x_scale, y_scale]
    if flip is True:
        filters += ["hflip, vflip"]
    if sub is True:
        filters += ["subtitles=%s" % subfile]

    command = [FFMPEG, "-loglevel", LOGLEVEL, "-ss", start, "-i", input_file,
               "-t", duration, "-r", fps, "-vf", ",".join(filters),
               os.path.join("./gif", "%08d.png")]

    if sub is False and flip is False and\
       x_scale is False and y_scale is False:
        command.pop(11)
        command.pop(11)

    run(command)
    return glob.glob(os.path.join(os.getcwd(), "gif", "*.png"))


def make_gif(output_file, fps=10):
    """ Creates the gif and optimises it """
    print "Creating gif (Call this 80%)"
    run([CONVERT, "-delay", str(100 / fps), os.path.join("gif", "*png"),
         output_file])
    print "Optimising (Call this 99%)"
    run([OPTIMISE, "-O3", "--colors", 256, "--batch", "-i", output_file])


def cleanup(frames, sub="sub.srt"):
    """ Deletes all files created """
    for frame in frames:
        os.unlink(frame)
    try:
        os.unlink(sub)
    except:
        pass


def create_gif(args):
    """ Calls functions to extract the frames and create the gif,
        then remove the frames """
    if args.subtitle_file is not False:
        args.subtitle = True

    if args.subtitle is True:
        args.subtitle_file = "sub.srt"
        #i = 1
        #while os.path.exists(args.subtitle_file):
        #    args.subtitle_file = "sub%r.srt" % i
        #    i =+ 1
        #del i
        extract_subs(args.input_file, args.subtitle_file)
        if args.subtitle_offset is False:
            offset_subs(args.subtitle_file, args.start)

    frames = get_frames(args.input_file, args.start, args.duration,
                        fps=args.fps, flip=args.flip, sub=args.subtitle,
                        subfile=args.subtitle_file, x_scale=args.x,
                        y_scale=args.y)
    make_gif(args.output_file, fps=args.fps)
    cleanup(frames, sub=args.subtitle_file)


def main(arguments):
    if arguments.use_builtin is True:
        CONVERT = "bin/convert"
        OPTIMISE = "gifsicle"
        FFMPEG = "ffmpeg"
    create_gif(arguments)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("input_file",
                        help="The input video file (anything ffmpeg supports)",
                        type=str)

    parser.add_argument("output_file", help="The name of the output gif.",
                        type=str)

    parser.add_argument("start", help="The time in seconds to start the gif",
                        type=float)

    parser.add_argument("duration", help="Duration to create the gif",
                        type=float)

    parser.add_argument("-f", "--flip", help="Flip the image upside down.",
                        action="store_true", default=False)

    parser.add_argument("-x", "-x-scale", help="Pixels wide the gif will be.\
If -x isn't set, it will keep it in proportion",
                        type=int, default=False)

    parser.add_argument("-y", "-y-scale", help="Pixels high the gif will bef.\
If -x isn't set, it will keep it in proportion",
                        type=int, default=False)

    parser.add_argument("-s", "--subtitle", help="Burn in the embedded (use\
--subtitle-file if not) subtitles to the video", action="store_true",
                        default=False)

    parser.add_argument("-so", "--subtitle-offset", help="Doesn't offset the\
subtitles to align with the video (Probably don't want this)",
                        action="store_true", default=False)

    parser.add_argument("-sf", "--subtitle-file", help="The subtitle file,\
for if there is not embedded subtitles, enables -s.", default=False, type=str)

    parser.add_argument("-b", "--use-builtin",
                        help="Use the system `convert`, `ffmpeg`\
and `gifsicle` commands.", action="store_true")

    parser.add_argument("-fps", "--fps", help="FPS of the gif", type=int,
                        default=8)

    arguments = parser.parse_args()
    main(arguments)
