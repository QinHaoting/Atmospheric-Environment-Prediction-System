import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['KaiTi', 'SimHei', 'FangSong']  # 汉字字体,优先使用楷体，如果找不到楷体，则使用黑体
plt.rcParams['font.size'] = 12  # 字体大小
plt.rcParams['axes.unicode_minus'] = False  # 正常显示负号

# x=[1,2,3,4,5,6,7,8,9]
x=["无持续风向","东北风","东风","西北风","北风","西风","东南风","西南风","南风"]
y=[919,524,335,297,216,157,154,128,68]
plt.bar(x,y)
plt.show()