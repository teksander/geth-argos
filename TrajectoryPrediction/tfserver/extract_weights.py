from keras.models import load_model
from ai import AI
import numpy as np
ai = AI(0, "")
model = ai.get_model()

print("testing")
print(model)
for i, layer in enumerate(model.layers):
    print(i)
    print(layer.name, layer.weights)
for i, v in enumerate(model.trainable_weights):
    print(i)
    print(v.numpy())
    