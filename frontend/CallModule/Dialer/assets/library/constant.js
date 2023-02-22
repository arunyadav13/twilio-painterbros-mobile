export const urls = {
  deviceAccessToken: {
    method: "POST",
    url: "/access-token"
  },
  getPreferences: {
    method: "POST",
    url: "/preferences"
  },
  updatePreferences: {
    method: "PUT",
    url: "/preferences"
  }
};

export const SECONDARY_DEVICE_INFO_MESSAGE =
  "You have one or more active calls on another device/tab. Please complete all the calls to start using this device.";
