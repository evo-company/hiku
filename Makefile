proto:
	python -m grpc_tools.protoc -I. --python_out=. hiku/protobuf/result.proto
	python -m grpc_tools.protoc -I. --python_out=. tests/protobuf/result.proto
