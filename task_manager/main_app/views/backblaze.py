from b2sdk.v1 import InMemoryAccountInfo, B2Api
from b2sdk.v1 import AbstractProgressListener
from b2sdk.v1 import escape_control_chars
from tqdm import tqdm

from django.conf import settings

class TqdmProgressListener(AbstractProgressListener):
    """
    Progress listener based on tqdm library.

    This listener displays a nice progress bar, but requires `tqdm` package to be installed.
    """

    def __init__(self, *args, **kwargs):
        if tqdm is None:
            raise ModuleNotFoundError("No module named 'tqdm' found")
        self.tqdm = None  # set in set_total_bytes()
        self.prev_value = 0
        super().__init__(*args, **kwargs)

    def set_total_bytes(self, total_byte_count: int) -> None:
        if self.tqdm is None:
            self.tqdm = tqdm(
                desc=escape_control_chars(self.description),
                total=total_byte_count,
                unit='B',
                unit_scale=True,
                leave=True,
                miniters=1,
                smoothing=0.1,
                mininterval=0.2,
            )

    def bytes_completed(self, byte_count: int) -> None:
        if self.prev_value < byte_count:
            self.tqdm.update(byte_count - self.prev_value)
            self.prev_value = byte_count

    def _can_change_description(self) -> bool:
        return self.tqdm is None

    def close(self) -> None:
        if self.tqdm is not None:
            self.tqdm.close()
        super().close()

def upload_to_backblaze(file_path: str, local_path: str = "") -> str | None:
    try:
        info = InMemoryAccountInfo()
        b2_api = B2Api(info)
        b2_api.authorize_account("production", settings.B2_APPLICATION_KEY_ID, settings.B2_APPLICATION_KEY)

        bucket = b2_api.get_bucket_by_name(settings.B2_BUCKET_NAME)

        progress_listener = TqdmProgressListener()
        main_file = bucket.upload_local_file(
            local_file=file_path,
            file_name=local_path,
            progress_listener=progress_listener,
        )
        print(f"File successfully uploaded: {main_file.id_}\n")
        return main_file.id_
    except Exception as e:
        print(e)
        return None

def delete_from_backblaze(link:str) -> bool:
    ...

if __name__ == "__main__":
    upload_to_backblaze("", "")
    ...