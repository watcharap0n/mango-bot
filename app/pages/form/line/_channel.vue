<template>

  <v-container
      class="d-flex justify-center"
  >
    <div class="d-flex flex-column justify-space-between align-center">
      <v-img
          :src="require('~/assets/images/mango-profile.jpg')"
          width="280"
      ></v-img>

      <v-card flat>

        <v-card-text>
          <div v-for="(v, k) in models">

            <div v-if="transaction.models[k]">
              <v-text-field
                  v-if="transaction.models[k].type_field === 'default'"
                  v-model="retrieves[v.value]"
                  color="success"
                  :label="transaction.models[k].text"
                  :outlined="transaction.models[k].outlined"
                  :rounded="transaction.models[k].rounded"
                  :solo="transaction.models[k].solo">
              </v-text-field>
            </div>

            <div v-if="transaction.models[k]">
              <v-select
                  v-if="transaction.models[k].type_field === 'select'"
                  :items="transaction.models[k].items_select"
                  v-model="retrieves[v.value]"
                  color="success"
                  item-color="success"
                  :outlined="transaction.models[k].outlined"
                  :rounded="transaction.models[k].rounded"
                  :solo="transaction.models[k].solo"
              ></v-select>
            </div>
          </div>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
              small
              color="success"
              dark
              @click="save"
          >
            submit
          </v-btn>

        </v-card-actions>

      </v-card>

    </div>
    <overlay :overlay="overlay"/>
  </v-container>

</template>

<script>
import liff from '@line/liff';
import Overlay from '@/components/app/Overlay'

export default {
  layout: 'public',

  components: {
    Overlay
  },

  data() {
    return {
      overlay: false,
      models: [],
      accessToken: '',
      transaction: {},
      retrieves: {},
    }
  },

  async created() {
    this.overlay = true;
    await this.getForm();
    await this.getDataTable();
    await this.initialized();
    this.overlay = false;
  },

  methods: {
    async initialized() {
      if (this.transaction.id_form) {
        await liff.init({liffId: this.transaction.id_form},
            () => {
              if (liff.isLoggedIn()) {
                liff.getProfile()
                    .then((profile) => {
                      console.log(profile)
                    })
              } else {
                liff.login();
              }
            });
      }
    },

    async getForm() {
      const path = `/form/find/${this.$route.params.channel}`
      await this.$axios.get(path)
          .then((res) => {
            this.transaction = res.data;
            this.accessToken = res.data.access_token;
          })
          .catch((err) => {
            console.error(err);
          })
    },

    async getDataTable() {
      let encoded = encodeURIComponent(this.accessToken);
      const path = `/data/table/find?access_token=${encoded}&default_field=false`
      await this.$axios.get(path)
          .then((res) => {
            this.models = res.data;
          })
          .catch((err) => {
            console.error(err);
          })
    },

    async notification() {
      const path = `/notification/post/condition/form?id=${this.$route.params.channel}`;
      this.$axios.post(path, this.retrieves)
          .then((res) => {
            console.log(res.data);
          })
          .catch((err) => {
            console.error(err);
          })
    },

    async save() {
      const path = `/retrieve/create/public?access_token=${this.accessToken}`;
      await this.$axios.post(path, this.retrieves)
          .then(() => {
            this.$swal.fire(
                'Thank you for submitting information.',
                'We will contact you back soon.',
                'success'
            )
            .then(()=>{
              if (this.transaction.id_form) {
                liff.closeWindow();
              }
            })
            this.notification();
          })
          .catch((err) => {
            this.$notifier.showMessage({
              content: `something wrong | status code ${err.response.status}`,
              color: 'red'
            })
          })
    }
  }


}
</script>

<style>

</style>