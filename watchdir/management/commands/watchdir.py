import os
import sys
import time
import shutil

from django.core.management.base import BaseCommand
from django.conf import settings

from sections.models import Section, VideoSection
from video.models import Video
from upload_video.utils import ensure_file_name_is_unique, clean_file_name


class Command(BaseCommand):
    help = 'Launch watchdir daemon'

    def handle(self, *args, **options):
        self.base_path = os.path.join(os.curdir, "ftp")
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

        try:
            while True:
                videos = {}
                sections_map = {}

                sections_map = self.update_directories_hierarchy()

                videos = self.parse_all_videos(videos, sections_map)

                self.handle_videos(videos)
                time.sleep(3)

        except KeyboardInterrupt:
            sys.exit(0)

    def update_directories_hierarchy(self):
        def _recursivly_generate_directories(base, section, childrens):
            path = os.path.join(base, section.title)
            partage = os.path.join(path, "PARTAGE")

            sections_map[path] = section
            if not os.path.exists(path):
                os.makedirs(path)

            if not os.path.exists(partage):
                os.makedirs(partage)

            for sub_section, sub_childrens in childrens:
                _recursivly_generate_directories(path, sub_section, sub_childrens)

        sections_map = {}
        for section, childrens in Section.objects.all().as_python_tree():
            _recursivly_generate_directories(self.base_path, section, childrens)

        return sections_map

    def parse_all_videos(self, videos, sections_map):
        for path in sections_map.keys():
            for name in os.listdir(path):
                file_path = os.path.join(path, name)

                if not os.path.isfile(file_path) or not file_path.lower().endswith(".mp4"):
                    continue

                # TODO partage/Vantage

                videos[file_path] = {
                    "name": name,
                    "section": sections_map[path],
                    "last_modification_time": time.time() - os.path.getmtime(file_path),
                    "send_notification": False,  # TODO Vantage
                }

        return videos

    def handle_videos(self, videos):
        for video_path, informations in videos.items():
            if informations["last_modification_time"] < 4:
                continue

            section = informations["section"]
            destination = os.path.join(settings.MEDIA_ROOT, "videos")
            file_name = informations["name"]

            file_name = clean_file_name(file_name)
            file_name = ensure_file_name_is_unique(destination, file_name)

            print "Detecting new video '%s', loading it into saya into the section '%s' as '%s'" % (video_path, section, file_name)

            shutil.move(
                src=video_path,
                dst=os.path.join(destination, file_name),
            )

            video = Video.objects.create(
                title=informations["name"][:-len(".mp4")],
                file_name=file_name,
            )

            VideoSection.objects.create(
                video=video,
                section=section,
            )
