import requests

url = "https://raw.githubusercontent.com/ultralytics/yolov5/master/data/images/zidane.jpg"
with open("test_image.jpg", "wb") as f:
    f.write(requests.get(url).content)
print("Downloaded test_image.jpg")
