"""ResNet18 sign classifier, Module 5's deep learning path: train on the robot's GPU from dataset/signs/, read signs live.

torch and torchvision come with the Yahboom JetPack image. They are imported inside the functions, so the rest of
the package (and the tests) work without them. ResNet18 starts from the ImageNet weights in
models/resnet18-f37072fd.pth, kept in the repo because the robot's hotspot has no internet.

Python 3.6 compatible (JetPack 4 on Jetson Nano).
"""
import glob
import os

import cv2

from .params import REPO_ROOT

MODEL_DIR = os.path.join(REPO_ROOT, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "sign_resnet18.pth")
WEIGHTS_NAME = "resnet18-f37072fd.pth"  # from https://download.pytorch.org/models/, as torchvision names it
WEIGHT_DIRS = (MODEL_DIR,
               os.path.expanduser("~/.cache/torch/hub/checkpoints"),  # torchvision 0.6 and later
               os.path.expanduser("~/.cache/torch/checkpoints"))  # older torchvision
INPUT_SIZE = 224
MEAN = (0.485, 0.456, 0.406)  # ImageNet statistics the pretrained weights expect
STD = (0.229, 0.224, 0.225)
TEST_SHARE = 0.2  # photos held back to measure accuracy after each epoch
BATCH_SIZE = 8  # small: the Nano's 4 GB is shared by the CPU, the GPU and the camera


def find_pretrained(dirs=WEIGHT_DIRS):
    """Path of the ImageNet resnet18-*.pth weights, or None when none of `dirs` has them."""
    for folder in dirs:
        found = sorted(glob.glob(os.path.join(folder, "resnet18-*.pth")))
        if found:
            return found[0]
    return None


def resnet18(num_classes, weights_path=None):
    """ResNet18 with a new last layer for our classes, starting from the ImageNet weights when given."""
    import torch
    import torchvision

    model = torchvision.models.resnet18(pretrained=False)
    if weights_path:
        model.load_state_dict(torch.load(weights_path, map_location="cpu"))
    model.fc = torch.nn.Linear(model.fc.in_features, num_classes)
    return model


def _device():
    import torch
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _accuracy(model, loader, device):
    import torch
    model.eval()
    right = total = 0
    with torch.no_grad():
        for images, labels in loader:
            guesses = model(images.to(device)).argmax(1).cpu()
            right += int((guesses == labels).sum())
            total += len(labels)
    return right / float(total)


def train(dataset_dir, model_path, epochs, on_epoch, should_stop, weights_path, lr=0.001):
    """Train on dataset_dir/<class>/*.jpg and keep the epoch with the best test accuracy in model_path.

    on_epoch(epoch, accuracy, best) reports progress; should_stop() is checked every batch. Returns the best
    accuracy (None if stopped before the first epoch ended).
    """
    import torch
    import torch.nn.functional as F
    from torchvision import datasets, transforms

    resize = [transforms.Resize((INPUT_SIZE, INPUT_SIZE)), transforms.ToTensor(), transforms.Normalize(MEAN, STD)]
    train_data = datasets.ImageFolder(dataset_dir, transforms.Compose(
        [transforms.ColorJitter(0.3, 0.3, 0.3, 0.05)] + resize))  # room lights differ from day to day
    test_data = datasets.ImageFolder(dataset_dir, transforms.Compose(resize))
    order = torch.randperm(len(train_data)).tolist()
    n_test = max(1, int(len(order) * TEST_SHARE))
    # num_workers=0: no forked loader processes next to the camera thread
    train_loader = torch.utils.data.DataLoader(torch.utils.data.Subset(train_data, order[n_test:]),
                                               batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
    test_loader = torch.utils.data.DataLoader(torch.utils.data.Subset(test_data, order[:n_test]),
                                              batch_size=BATCH_SIZE, num_workers=0)
    device = _device()
    model = resnet18(len(train_data.classes), weights_path).to(device)
    optimizer = torch.optim.SGD(model.parameters(), lr=lr, momentum=0.9)
    best = None
    try:
        for epoch in range(1, epochs + 1):
            model.train()
            for images, labels in train_loader:
                if should_stop():
                    return best
                optimizer.zero_grad()
                loss = F.cross_entropy(model(images.to(device)), labels.to(device))
                loss.backward()
                optimizer.step()
            accuracy = _accuracy(model, test_loader, device)
            if best is None or accuracy > best:
                best = accuracy
                _save(model, train_data.classes, model_path)
            on_epoch(epoch, accuracy, best)
        return best
    finally:
        del model, optimizer
        if torch.cuda.is_available():
            torch.cuda.empty_cache()  # give the GPU memory back to live reading


def _save(model, classes, model_path):
    """Write to a temporary file first, so a crash mid-save never leaves a broken model behind."""
    import torch
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    tmp = model_path + ".tmp"
    torch.save({"classes": list(classes), "state_dict": model.state_dict()}, tmp)
    os.replace(tmp, model_path)


class SignClassifier:
    """A model saved by train(), on the GPU when there is one. predict(frame) gives (label, confidence)."""

    def __init__(self, model_path=MODEL_PATH):
        import torch
        # shortcut: torch.load unpickles; only load files train() wrote. JetPack 4's torch predates weights_only=True
        saved = torch.load(model_path, map_location="cpu")
        self.classes = list(saved["classes"])
        self.device = _device()
        model = resnet18(len(self.classes))
        model.load_state_dict(saved["state_dict"])
        self.model = model.to(self.device).eval()

    def predict(self, frame):
        """(label, confidence 0-1) for a BGR camera frame, preprocessed the same way as in train()."""
        import torch
        rgb = cv2.cvtColor(cv2.resize(frame, (INPUT_SIZE, INPUT_SIZE)), cv2.COLOR_BGR2RGB)
        x = torch.from_numpy(rgb).to(self.device).permute(2, 0, 1).float().div(255.0)
        mean = torch.tensor(MEAN, device=self.device).view(3, 1, 1)
        std = torch.tensor(STD, device=self.device).view(3, 1, 1)
        with torch.no_grad():
            probs = torch.softmax(self.model(((x - mean) / std).unsqueeze(0)), dim=1)[0]
        confidence, index = probs.max(0)
        return self.classes[int(index)], float(confidence)
