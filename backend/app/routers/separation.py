from fastapi import APIRouter, UploadFile, File
import spleeter.separator

router = APIRouter()

@router.post("/")
async def separate(
    audio_file: UploadFile = File(...)
):
    # save uploaded file to disk
    input_path = f"/tmp/{audio_file.filename}"
    with open(input_path, "wb") as f:
        f.write(await audio_file.read())

    # run spleeter (2-stems: vocals vs accompaniment)
    separator = spleeter.separator.Separator('spleeter:2stems')
    separator.separate_to_file(input_path, '/tmp/output/')

    return {
        "vocals": "/tmp/output/vocals.wav",
        "accompaniment": "/tmp/output/accompaniment.wav"
    }