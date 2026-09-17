<template>
  <div class="scale-page">
    <el-alert type="info" :closable="false" style="margin-bottom: 16px">
      对照百万级 AIoT 平台演进路径评估当前部署。参考
      <a href="https://mp.weixin.qq.com/s/Hc878kPSOXpb-rm-QTd3dw" target="_blank" rel="noopener">设备量级迭代与技术选型</a>
    </el-alert>

    <el-row :gutter="16">
      <el-col :span="8">
        <el-card v-loading="loading">
          <template #header>当前档位</template>
          <div class="stage-name">{{ profile.stage_meta?.name || '—' }}</div>
          <el-descriptions :column="1" size="small" border style="margin-top: 12px">
            <el-descriptions-item label="可见设备">{{ profile.device_count ?? 0 }}</el-descriptions-item>
            <el-descriptions-item label="Redis 在线缓存">{{ profile.online_cached ?? 0 }}</el-descriptions-item>
            <el-descriptions-item label="Broker">{{ profile.capabilities?.mqtt_host || '—' }}</el-descriptions-item>
            <el-descriptions-item label="Influx">{{ profile.capabilities?.influx ? '已启用' : '未启用' }}</el-descriptions-item>
            <el-descriptions-item label="Redis">{{ profile.capabilities?.redis ? '可用' : '不可用' }}</el-descriptions-item>
            <el-descriptions-item label="连接限流">{{ profile.capabilities?.connect_rate_limit || 0 }} /s</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
      <el-col :span="16">
        <el-card>
          <template #header>目标指标（百万级）</template>
          <el-descriptions :column="3" border size="small">
            <el-descriptions-item label="在线设备">{{ profile.targets?.devices }}</el-descriptions-item>
            <el-descriptions-item label="消息吞吐">{{ profile.targets?.tps }}</el-descriptions-item>
            <el-descriptions-item label="端到端延迟">&lt; {{ profile.targets?.latency_ms }}ms</el-descriptions-item>
            <el-descriptions-item label="可用性">{{ profile.targets?.availability }}</el-descriptions-item>
            <el-descriptions-item label="OTA 成功率">{{ profile.targets?.ota_success }}</el-descriptions-item>
          </el-descriptions>
          <el-alert
            v-if="profile.gaps?.length"
            type="warning"
            :closable="false"
            style="margin-top: 12px"
            :title="'缺口：' + profile.gaps.join('；')"
          />
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 16px">
      <template #header>架构演进路径</template>
      <el-table :data="profile.stages || []" stripe>
        <el-table-column prop="name" label="阶段" width="180" />
        <el-table-column prop="devices" label="设备量级" width="120" />
        <el-table-column prop="tps" label="吞吐" width="100" />
        <el-table-column prop="stack" label="推荐栈" />
        <el-table-column prop="this_repo" label="本仓库落地" />
        <el-table-column label="" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.id === profile.stage" type="success" size="small">当前</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card style="margin-top: 16px">
      <template #header>
        消息流水线
        <span class="stat">Stream {{ profile.pipeline_stats?.stream ?? 0 }} · DLQ {{ profile.pipeline_stats?.dlq ?? 0 }} · 告警防抖 {{ profile.pipeline_stats?.alert_debounce_s ?? 60 }}s</span>
      </template>
      <el-table :data="profile.pipeline || []" stripe>
        <el-table-column prop="step" label="#" width="50" />
        <el-table-column prop="name" label="环节" width="120" />
        <el-table-column prop="now" label="本仓库实现" />
      </el-table>
    </el-card>

    <el-card style="margin-top: 16px">
      <template #header>当前档位动作清单</template>
      <ul class="playbook">
        <li v-for="(item, i) in (profile.playbook || [])" :key="i">{{ item }}</li>
      </ul>
    </el-card>

    <el-card style="margin-top: 16px">
      <template #header>技术选型对照</template>
      <el-table :data="profile.selection || []" stripe>
        <el-table-column prop="area" label="领域" width="140" />
        <el-table-column prop="recommend" label="百万级建议" />
        <el-table-column prop="now" label="本系统现状" />
      </el-table>
    </el-card>

    <el-card style="margin-top: 16px">
      <template #header>协议选型</template>
      <el-table :data="profile.protocols || []" stripe>
        <el-table-column prop="scene" label="场景" width="160" />
        <el-table-column prop="recommend" label="推荐协议" width="180" />
        <el-table-column prop="reason" label="理由" />
      </el-table>
    </el-card>

    <el-card style="margin-top: 16px">
      <template #header>避坑</template>
      <el-table :data="profile.pitfalls || []" stripe>
        <el-table-column prop="pit" label="坑" width="120" />
        <el-table-column prop="why" label="原因" />
        <el-table-column prop="fix" label="本系统对策" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { getScaleProfile } from '@/api/modules/scale'

const loading = ref(false)
const profile = ref({})

onMounted(async () => {
  loading.value = true
  try {
    profile.value = await getScaleProfile()
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.stage-name { font-size: 20px; font-weight: 600; color: #303133; }
a { color: #409eff; }
.stat { float: right; font-size: 13px; color: #909399; font-weight: normal; }
.playbook { margin: 0; padding-left: 20px; line-height: 1.8; color: #606266; }
</style>
