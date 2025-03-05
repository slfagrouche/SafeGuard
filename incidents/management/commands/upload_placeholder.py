from django.core.management.base import BaseCommand
from incidents.s3 import s3_manager
import base64

class Command(BaseCommand):
    help = 'Uploads a placeholder image to S3'

    def handle(self, *args, **options):
        # Simple 1x1 pixel transparent PNG
        TRANSPARENT_PIXEL = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

        try:
            # Decode base64 image
            image_bytes = base64.b64decode(TRANSPARENT_PIXEL)
            
            # Upload to S3 with specific path
            image_url = s3_manager.upload_image(
                image_bytes,
                'image/png',
                'static/incidents/images/placeholder.png'
            )
            
            if image_url:
                self.stdout.write(self.style.SUCCESS(f'Successfully uploaded placeholder image: {image_url}'))
            else:
                self.stdout.write(self.style.ERROR('Failed to upload placeholder image'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
