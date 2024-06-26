from fastapi import FastAPI, File, UploadFile, HTTPException
import torch as torch
from PIL import Image
import shutil
from fastapi.responses import FileResponse
import uvicorn
from pathlib import Path
import io

app = FastAPI()

torch.hub._validate_not_a_forked_repo=lambda a,b,c: True
model = torch.hub.load('ultralytics/yolov5', 'custom', path='last.pt', force_reload=True)


class ModelClass:  # класс, определяющий тип возвращаемого изображения при запросе
    def __init__(self, mode='Default', last_im=None, last_im_name=None):
        self.mode = mode
        self.last_im = last_im
        self.last_im_name = last_im_name


model_class = ModelClass()


@app.get('/check')  # метод для проверки работает ли сервис в данный момент
def check_func():
    try:
        return "Всё работает"
    except:
        return HTTPException(status_code=500, detail='Не работает :(')


@app.get('/help')  # вызов справки
def help_func():
    objects = "small vehicle, large vehicle, tennis court, ground track field, ship, harbor, storage tank," \
              "swimming pool, plane, bridge, roundabout, baseball diamond, soccer ball field, basketball court, " \
              "helicopter"

    return f"Наша модель классифицирует следующие объекты:{objects}. На примере Postman, Чтобы получить " \
           f"изображение с классифицией объектов, отправь файл, являющийся изображением в формате .png или .jpg. " \
           f"(Params: Body, type of key: File, параметр: file), пример запроса: http://0.0.0.0:8000/uploadfile/. " \
           f"Доступные команды сервиса: " \
           f"GET: /check/ - проверка статуса работы сервиса; " \
           f"GET: /help/ - справка; " \
           f"POST: /uploadfile/ - отправка изображения и получение его с применённой классификацией; " \
           f"POST: /mode/ - параметр gray - модель будет возвращать чёрно-белые изображения, параметр default - ; " \
           f"обычныеPOST: /"


@app.get('/last')  # получить информацию о последнем загруженном изображении
async def get_last_image():
    if model_class.last_im is None:
        return "Вы пока не загрузили ни одного изображения. Доступные команды смотрите по /help"
    else:
        return {'filename': model_class.last_im_name, 'size': model_class.last_im.size}


@app.post("/mode")
async def change_mode(mode: str) -> str:
    if mode == 'gray' or mode == 'Gray':
        model_class.mode = 'L'
        return 'Модель будет возвращать чёрно-белые изображения'
    elif mode == 'default' or mode == 'Default':
        model_class.mode = 'Default'
        return 'Модель будет возвращать обычные изображения'
    else:
        return HTTPException(status_code=400, detail='BAD REQUEST. Возможные параметры запроса: {gray} или {default}')


@app.post("/uploadfile")
async def create_upload_file(file: UploadFile = File(...)):
    try:
        shutil.rmtree("runs\detect\exp")  # после отправки удаляю фолдер, чтобы не засорять папку
    except:  # если это первый запуск, удаление не произойдёт и мы идём далее
        pass
    try:
        im = Image.open(file.file)  # проверяем является ли файл изображением
        model_class.last_im_name = file.filename
        model_class.last_im = im
        if model_class.mode == 'L':  # перекрашиваем в черно-белый если юзер менял мод работы
            im = im.convert("L")
    except Exception:
        raise HTTPException(status_code=500, detail='File must be an image (.png or .jpg)')
    results = model(im)
    img = results.render()
    img = Image.fromarray(img[0], 'RGB')
    img.save('my.png')
    path = Path("my.png")
    return FileResponse(path)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
