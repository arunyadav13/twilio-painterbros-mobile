import React from "react";
import { Button, Image } from "react-native";
import addcallicon from "../assets/images/addcallicon.svg";
const { REACT_APP_STATIC_ASSETS_BASE_URL } = process.env;

class AddNewParticipantButton extends React.Component {
  constructor(props) {
    super(props);
  }
  render() {
    const { conferenceSid, user, callSid, from_, addNewParticipant, disabled } =
      this.props;
    return (
      <Button
        className="removecolorbut addcallicon"
        onPress={() =>
          addNewParticipant(conferenceSid, user.identity, callSid, from_)
        }
        disabled={disabled}
      >
        <Image alt="" source={`${REACT_APP_STATIC_ASSETS_BASE_URL}${addcallicon}`} />
        <h4>Add call</h4>
      </Button>
    );
  }
}

export default AddNewParticipantButton;
