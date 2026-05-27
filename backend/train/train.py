from ultralytics import YOLO

# 1. 换用中杯模型，平衡速度与精度
model = YOLO("yolo11m.pt") 

results = model.train(
    data="VisDrone.yaml", 
    epochs=150, 
    imgsz=1024,       
    batch=32,          
    device="0",        
    workers=16,        
    cache=False,        
    mosaic=0.3,        
    mixup=0.1,         
    copy_paste=0.2,    
    optimizer="auto",
    patience=30        
)