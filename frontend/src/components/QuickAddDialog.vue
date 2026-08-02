<script setup lang="ts">
// 快速登记：工作台一键弹窗，30 秒记一条留底，支持连续录入（个人台账核心操作）。
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, FormInstance } from 'element-plus'
import { maintenanceApi, meetingApi } from '@/api'
import { useConfigStore } from '@/stores/config'

const props = defineProps<{ visible: boolean }>()
const emit = defineEmits<{ (e: 'update:visible', v: boolean): void; (e: 'saved'): void }>()

const router = useRouter()
const config = useConfigStore()
const formRef = ref<FormInstance>()
const submitting = ref(false)
const bizType = ref<'maintenance' | 'meeting'>('maintenance')
const form = reactive({
  category: '',
  requester: '',
  location: '',
  problem_description: '',
  result: '',
  status: 'pending',
  meeting_name: '',
  meeting_time: '' as string,
})

const categoryGroups = computed(() => config.categoryGroups())

function resetForm() {
  Object.assign(form, {
    category: '', requester: '', location: '', problem_description: '', result: '',
    status: 'pending', meeting_name: '', meeting_time: '',
  })
  formRef.value?.clearValidate()
}

async function submit(continueNext: boolean) {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      if (bizType.value === 'maintenance') {
        await maintenanceApi.create({
          category: form.category,
          requester: form.requester,
          location: form.location,
          problem_description: form.problem_description,
          result: form.result,
          status: form.status,
        })
      } else {
        await meetingApi.create({
          meeting_name: form.meeting_name,
          meeting_time: form.meeting_time || null,
          status: form.status,
        })
      }
      ElMessage.success(continueNext ? '已保存，继续登记' : '已保存')
      emit('saved')
      if (continueNext) {
        resetForm()
      } else {
        emit('update:visible', false)
      }
    } finally {
      submitting.value = false
    }
  })
}

onMounted(() => {
  config.fetch()
})
</script>

<template>
  <el-dialog
    :model-value="visible"
    :title="bizType === 'maintenance' ? '快速登记 · 维护记录' : '快速登记 · 会议调试'"
    width="560px"
    :close-on-click-modal="false"
    @update:model-value="(v: boolean) => emit('update:visible', v)"
    @closed="resetForm"
  >
    <el-segmented
      v-model="bizType"
      :options="[
        { label: '维护记录', value: 'maintenance' },
        { label: '会议调试', value: 'meeting' },
      ]"
      style="margin-bottom: 16px"
    />

    <el-form ref="formRef" :model="form" label-width="90px" @submit.prevent>
      <template v-if="bizType === 'maintenance'">
        <el-form-item label="分类" prop="category" :rules="[{ required: true, message: '请选择分类', trigger: 'change' }]">
          <el-select v-model="form.category" placeholder="选择分类" filterable style="width: 100%">
            <el-option-group v-for="g in categoryGroups" :key="g.label" :label="g.label">
              <el-option v-for="c in g.options" :key="c" :label="c" :value="c" />
            </el-option-group>
          </el-select>
        </el-form-item>
        <el-form-item label="报修人" prop="requester" :rules="[{ required: true, message: '请输入报修人', trigger: 'blur' }]">
          <el-input v-model="form.requester" placeholder="谁报修 / 报障人" />
        </el-form-item>
        <el-form-item label="地点">
          <el-input v-model="form.location" placeholder="可选" />
        </el-form-item>
        <el-form-item label="问题描述" prop="problem_description" :rules="[{ required: true, message: '请填写问题', trigger: 'blur' }]">
          <el-input v-model="form.problem_description" type="textarea" :rows="2" placeholder="什么问题 / 做什么" />
        </el-form-item>
        <el-form-item label="处理结果">
          <el-input v-model="form.result" type="textarea" :rows="2" placeholder="已处理完成可填写，未处理可留空" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio value="pending">待处理</el-radio>
            <el-radio value="processing">处理中</el-radio>
            <el-radio value="resolved">已解决</el-radio>
          </el-radio-group>
        </el-form-item>
      </template>

      <template v-else>
        <el-form-item label="会议名称" prop="meeting_name" :rules="[{ required: true, message: '请输入会议名称', trigger: 'blur' }]">
          <el-input v-model="form.meeting_name" placeholder="会议 / 调试任务名称" />
        </el-form-item>
        <el-form-item label="时间">
          <el-date-picker v-model="form.meeting_time" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" style="width: 100%" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio value="pending">待调试</el-radio>
            <el-radio value="debugged">已调试</el-radio>
            <el-radio value="completed">已完成</el-radio>
          </el-radio-group>
        </el-form-item>
      </template>
    </el-form>

    <template #footer>
      <el-button @click="emit('update:visible', false)">取消</el-button>
      <el-button type="primary" plain :loading="submitting" @click="submit(true)">
        保存并继续
      </el-button>
      <el-button type="primary" :loading="submitting" @click="submit(false)">保存</el-button>
    </template>
  </el-dialog>
</template>
