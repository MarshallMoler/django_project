# 1. 导入: 在需要使用的位置导入
import logging

# 2. 创建日志记录器: 导入后创建日志器才能使用
logger = logging.getLogger('django')

# 3. 根据不同情况, 输出日志
logger.debug('调试信息')
logger.info('打印信息')
logger.error('错误信息')