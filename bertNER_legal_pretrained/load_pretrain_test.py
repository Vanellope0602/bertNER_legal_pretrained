from tensorflow.python import pywrap_tensorflow

checkpoint_path = "./legal_electra_base/legal_electra_base.ckpt"
reader = pywrap_tensorflow.NewCheckpointReader(checkpoint_path)
vars = reader.get_variable_to_shape_map()
for v in vars:
    v_name = v
    var_tensor = reader.get_tensor(v)

    print("tensor name = ", v)
    print("tensor shape = ", var_tensor.shape)
    print("tensor value = ", var_tensor)
