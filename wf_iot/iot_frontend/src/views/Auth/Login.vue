<template>
    <div class="login-container">
      <h2>Login</h2>
      <from @sumbit.prevent="handleLogin">
        <div class="form-group">
          <label for="username">username:</label>
          <input type="text" id="username" v-model="username" required />
        </div>
        <div class="form-group">
          <label for="password">Password:</label>
          <input type="password" id="password" v-model="password" required />
        </div>
        <button type="submit">Loging:</button>
        <p v-if="error" class="error-message">{{ error }} </p>
      </from>
    </div>
  </template>
  
  <script>
  import { ref } from 'vue'
  import { useRouter } from 'vue-router'
  import { login } from '@/api/modules/auth'; // 假设API封装在api/modules/auth.js
  
  export default {
    name: 'Login',
    setup() {
      const username = ref('');
      const password = ref('');
      const error = ref('');
      const router = useRouter();
  
      const handleLogin = async () => {
        try {
          const response = await login(username.value, password.value);
        } catch (error) {
          error.value = 'Login failed. Please check your credentials.';
          console.error(err);
        }
      };
  
      return {
        username,
        password,
        error,
        handleLogin,
      }
    }
  }
  </script>
  
  <style>
  /*样式省略*/
  </style>