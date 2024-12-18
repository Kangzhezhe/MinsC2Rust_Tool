# sudo rm ./build/* -rf
# sudo rm ./rust_ast_project/target -rf

cd build
cmake ..
make -j16
# ctest --rerun-failed --output-on-failure