<template>
  <div>
    <v-row justify="center" class="text-center p-36">
      <v-col
          cols="12"
          sm="10"
          md="8"
          lg="6"
      >
        <v-card
            width="650"
        >
          <div class="d-flex flex-column justify-space-between align-center">
            <v-img
                max-height="400"
                max-width="250"
                :src="require('~/assets/images/mango-profile.jpg')"
            >
            </v-img>
          </div>
          <v-card-text>
            <v-form
                ref="form"
                v-model="valid"
                lazy-validation
            >
              <v-text-field
                  :rules="nameRules"
                  v-model="elements.name"
                  label="Name"
              ></v-text-field>
              <v-text-field
                  :rules="accessRules"
                  v-model="elements.access_token"
                  label="Access Token"
              >
              </v-text-field>
              <v-text-field
                  :rules="secretRules"
                  v-model="elements.secret_token"
                  label="Secret Token"
              >
              </v-text-field>
              <v-btn
                  x-large
                  style="width:200px"
                  color="#12AE7E"
                  rounded
                  dark
                  @click="submit"
                  :loading="!spinChannel"
                  :disabled="!valid"
              >Save
              </v-btn>
              <div class="p-8">
                <v-row justify="center">
                  <p>How to install and use </p>&nbsp;
                  <p>Platform CHATBOT</p>
                </v-row>
              </div>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script>

export default {
  layout: 'index',
  data() {
    return {
      spinChannel: true,
      copied: false,
      link: '',
      elements: {
        secret_token: '',
        name: '',
        access_token: '',
      },
      valid: true,
      nameRules: [
        v => !!v || 'please enter your name.',
      ],
      accessRules: [
        v => !!v || 'please enter your secret token.',
      ],
      secretRules: [
        v => !!v || 'please enter your access token.',
      ],
    }
  },
  methods: {
    submit() {
      this.spinChannel = false
      let form = this.$refs.form.validate();
      if (form) {
        this.save()
      } else {
        this.$notifier.showMessage({
          content: 'Please complete the information.',
          color: 'red'
        })
        this.spinChannel = false
      }
    },
    async save() {
      const path = '/callback/channel/create'
      await this.$axios.post(path, this.elements)
          .then(() => {
            this.$notifier.showMessage({
              content: `Your channel ${this.elements.name}.`,
              color: 'info'
            })
            this.spinChannel = true
            this.$router.push('/')
          })
          .catch((err) => {
            let status = err.response.status
            if (status === 401) {
              this.$notifier.showMessage({
                content: 'Invalid Access Token',
                color: 'red'
              })
            } else if (err.response.status === 400) {
              this.$notifier.showMessage({
                content: 'Access token already registered',
                color: 'red'
              })
            }
            console.error(err)
            this.spinChannel = true
          })
    },

  },
}
</script>

<style scoped>
.done {
  text-decoration: line-through;
}
</style>