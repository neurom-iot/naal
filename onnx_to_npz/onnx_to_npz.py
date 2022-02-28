import onnx

onnx_model = onnx.load('./model/lenet-1.onnx')

try:
	onnx.checker.check_model(onnx_model)
except onnx.checker.ValidationError as e:
	print('The model is invalid : %s' % e)
else:
	print('The model is valid!')

print(type(onnx_model))

print(onnx_model)
