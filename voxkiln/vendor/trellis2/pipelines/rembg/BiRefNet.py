from typing import *
from transformers import AutoModelForImageSegmentation
import torch
from torchvision import transforms
from PIL import Image


class BiRefNet:
    def __init__(self, model_name: str = "ZhengPeng7/BiRefNet"):
        # voxkiln license gate (research 43/45): the HF pipeline config asks
        # for briaai/RMBG-2.0, whose weights are CC BY-NC (commercial use
        # needs a BRIA license). The MIT-licensed BiRefNet weights are used
        # instead, unconditionally.
        if "RMBG" in str(model_name).upper():
            print(f"[voxkiln] rembg weights '{model_name}' are CC BY-NC; using ZhengPeng7/BiRefNet (MIT) instead")
            model_name = "ZhengPeng7/BiRefNet"
        self.model = AutoModelForImageSegmentation.from_pretrained(
            model_name, trust_remote_code=True
        )
        self.model.eval()
        self.transform_image = transforms.Compose(
            [
                transforms.Resize((1024, 1024)),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ]
        )
    
    def to(self, device: str):
        self.model.to(device)

    def cuda(self):
        self.model.cuda()

    def cpu(self):
        self.model.cpu()
        
    def __call__(self, image: Image.Image) -> Image.Image:
        image_size = image.size
        input_images = self.transform_image(image).unsqueeze(0).to(next(self.model.parameters()).device)
        # Prediction
        with torch.no_grad():
            preds = self.model(input_images)[-1].sigmoid().cpu()
        pred = preds[0].squeeze()
        pred_pil = transforms.ToPILImage()(pred)
        mask = pred_pil.resize(image_size)
        image.putalpha(mask)
        return image
    