from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from PIL import Image

from .forms import PlayerProfileForm


def image_upload(name="avatar.jpg", image_format="JPEG"):
    buffer = BytesIO()
    Image.new("RGB", (8, 8), "blue").save(buffer, format=image_format)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="text/plain")


class ProfileUploadTests(SimpleTestCase):
    def test_profile_upload_is_validated_from_bytes_and_normalized(self):
        form = PlayerProfileForm(files={"foto": image_upload()})

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["foto"].content_type, "image/png")
        self.assertTrue(form.cleaned_data["foto"].name.endswith(".png"))

    def test_profile_upload_rejects_non_image_bytes_even_with_image_extension(self):
        upload = SimpleUploadedFile(
            "avatar.jpg", b"not an image", content_type="image/jpeg"
        )

        form = PlayerProfileForm(files={"foto": upload})

        self.assertFalse(form.is_valid())
        self.assertIn("beschadigde afbeelding", str(form.errors))
