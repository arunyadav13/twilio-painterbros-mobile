import React from "react";
import { Button, Image,Text } from "react-native";
import { getWarmTransferParticipant } from "../assets/library/helper";
import warmtransfercomplete from "../../../Dialer/CallListContainer/assets/images/warmtransfercomplete.svg";
const { REACT_APP_STATIC_ASSETS_BASE_URL } = process.env;
class CompleteTransferButton extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    const { checkIfAllCallsYetToAnswer, callElement, completeTransferCall } =
      this.props;
    return (
      <Button
        className="removecolorbut "
        disabled={
          checkIfAllCallsYetToAnswer(callElement) > 0 ||
          window.shouldDisableTransferActionBtn
        }
        onPress={() => {
          window.shouldDisableTransferActionBtn = true;
          completeTransferCall(
            callElement,
            getWarmTransferParticipant(callElement)
          );
        }}
      >
        <Image
          source={`${REACT_APP_STATIC_ASSETS_BASE_URL}${warmtransfercomplete}`}
        />
        <Text>Complete Transfer</Text>
      </Button>
    );
  }
}

export default CompleteTransferButton;
