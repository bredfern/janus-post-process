#!/usr/bin/python3

import argparse
import os
import pathlib
import subprocess
import tempfile
import time
import itertools

import boto3
import pika

parser = argparse.ArgumentParser()

parser.add_argument(
    "--mjr-directory",
    help="location of mjr files to process",
    default="/DATA/janus-media/recordings",
)

parser.add_argument(
    "--archive-directory",
    help="location to write processed webm files",
    default="/DATA/janus-media/archive",
)

parser.add_argument(
    "--rabbitmq-url",
    help="url for rabbitmq connection",
    required=True,
)

parser.add_argument(
    "--rabbitmq-queue",
    help="name of the rabbitmq queue",
    default="janus-post-process",
)

parser.add_argument(
    "--janus-pp",
    help="location of the janus post processor on the system",
    default="/opt/janus/bin/janus-pp-rec",
)

parser.add_argument(
    "--s3-bucket",
    help="name of the s3 bucket to use",
    default="",
)

parser.add_argument(
    "--remove-source-media",
    help="remove mjr files after processing",
    action="store_true",
)

args = parser.parse_args()

output_extensions = {
    "audio": "opus",
    "video": "webm",
}

mjr_directory = pathlib.Path(args.mjr_directory)
archive_directory = pathlib.Path(args.archive_directory)


def callback(ch, method, properties, body):
    session_id = body.decode('UTF-8')
    media = list(mjr_directory.glob("*-{}*.mjr".format(session_id)))
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmpdir = pathlib.Path(tmpdirname)
        to_stitch = []
        audio_stitch = []
        video_stitch = []

        for m in sorted(media, key=lambda s: s.name.split("-")[4]):
            extension = output_extensions[m.stem.split("-")[-1]]
            tmp_dest = tmpdir.joinpath("{}.{}".format(m.stem, extension))
            subprocess.run([args.janus_pp, str(m), str(tmp_dest)])
            if tmp_dest.is_file():
                if str(tmp_dest).endswith(".webm"):
                    video_stitch.append(str(tmp_dest))
                else:
                    audio_stitch.append(str(tmp_dest))

        for a, v in zip(audio_stitch, video_stitch):
            tmp_archive_name = "{}-{}-archive-tmp.webm".format(
                session_id, time.time())
            tmp_archive = tmpdir.joinpath(
                session_id, tmp_archive_name)
            tmp_merge_cmd = ["/usr/bin/mkvmerge", "-w",
                             "-o", str(tmp_archive), a, v]
            to_stitch.append(str(tmp_archive))
            subprocess.run(tmp_merge_cmd)

        archive_name = "{}.webm".format(session_id)
        archive = archive_directory.joinpath(session_id, archive_name)
        merge_cmd = ["/usr/bin/mkvmerge", "-w", "-o",
                     str(archive), "["] + to_stitch + ["]"]
        subprocess.run(merge_cmd)
        # current bucket has no upload permission
        if args.s3_bucket != '':
            s3 = boto3.resource('s3')
            with archive.open('rb') as data:
                s3.Bucket(args.s3_bucket).upload_fileobj(data, archive.name)

    if args.remove_source_media:
        for m in media:
            m.unlink()


parameters = pika.URLParameters(args.rabbitmq_url)
connection = pika.BlockingConnection(
    parameters=pika.URLParameters(args.rabbitmq_url))
channel = connection.channel()
channel.queue_declare(queue=args.rabbitmq_queue)
channel.basic_consume(callback, queue=args.rabbitmq_queue, no_ack=True)
channel.start_consuming()
