cmake_minimum_required(VERSION 3.8)
project(car_bot_urdf)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# 寻找构建系统
find_package(ament_cmake REQUIRED)

# ---------------------------------------------------------
# 关键步骤：安装资源文件
# 这会将 launch, meshes, urdf 文件夹复制到 install/share/board 下
# 这样 package://board/meshes/... 路径才能生效
# ---------------------------------------------------------
install(DIRECTORY
  launch
  rviz
  meshes
  urdf
  config
  world
  map
  DESTINATION share/${PROJECT_NAME}
)
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()


ament_package()
