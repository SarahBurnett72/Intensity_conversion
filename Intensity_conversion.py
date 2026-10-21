
import math


import streamlit as st
import pandas as pd
import numpy as np


# --------------------------------------------------
# Constants
# --------------------------------------------------
H = 6.62607015e-34       # Planck constant, J s
C = 299792458            # Speed of light, m/s
NA = 6.02214076e23       # Avogadro constant, mol^-1
K_M = 683.0              # Maximum photopic efficacy, lm/W

st.set_page_config(
    page_title="Optical Unit Converter",
    page_icon="💡",
    layout="centered",
)

# Approximate CIE 1931 photopic luminous efficiency V(lambda).
# Values are sampled at 10 nm intervals.
# For precision applications, use the official CIE table.
CIE_VALUES = {
    380: 0.000039, 390: 0.000120, 400: 0.000396,
    410: 0.001210, 420: 0.004000, 430: 0.011600,
    440: 0.023000, 450: 0.038000, 460: 0.060000,
    470: 0.091000, 480: 0.139020, 490: 0.208020,
    500: 0.323000, 510: 0.503000, 520: 0.710000,
    530: 0.862000, 540: 0.954000, 550: 0.995000,
    560: 0.995000, 570: 0.952000, 580: 0.870000,
    590: 0.757000, 600: 0.631000, 610: 0.503000,
    620: 0.381000, 630: 0.265000, 640: 0.175000,
    650: 0.107000, 660: 0.061000, 670: 0.032000,
    680: 0.017000, 690: 0.008210, 700: 0.004102,
    710: 0.002091, 720: 0.001047, 730: 0.000520,
    740: 0.000249, 750: 0.000120, 760: 0.000060,
    770: 0.000030, 780: 0.000015,
}


def photopic_efficiency(wavelength_nm):
    """Approximate CIE V(lambda) by linear interpolation."""
    wavelengths = np.array(list(CIE_VALUES.keys()), dtype=float)
    efficiencies = np.array(list(CIE_VALUES.values()), dtype=float)

    if not 380 <= wavelength_nm <= 780:
        raise ValueError(
            "This approximation supports wavelengths from 380 to 780 nm."
        )

    return float(np.interp(
        wavelength_nm, wavelengths, efficiencies
    ))


def calculate_conversions(
    value, input_unit, wavelength_nm, solid_angle_sr
):
    """
    Convert between:
      - microeinstein/s (micromoles of photons/s)
      - W
      - mW
      - cd

    Assumes monochromatic light and a uniform luminous intensity
    over the specified solid angle for the cd conversion.
    """
    if value < 0:
        raise ValueError("Intensity must be non-negative.")

    if wavelength_nm <= 0:
        raise ValueError("Wavelength must be positive.")

    # Convert the selected input to radiant power in watts.
    if input_unit == "Microeinstein (µE/s)":
        # 1 µmol photons/s = 1e-6 mol photons/s
        photon_flux = value * 1e-6 * NA
        energy_per_photon = H * C / (wavelength_nm * 1e-9)
        power_w = photon_flux * energy_per_photon

    elif input_unit == "Watt (W)":
        power_w = value

    elif input_unit == "Milliwatt (mW)":
        power_w = value / 1000.0

    elif input_unit == "Candela (cd)":
        if solid_angle_sr <= 0:
            raise ValueError(
                "Solid angle must be greater than zero."
            )

        v_lambda = photopic_efficiency(wavelength_nm)

        if v_lambda <= 0:
            raise ValueError(
                "Photopic efficiency is zero at this wavelength."
            )

        # I_v = K_m * V(lambda) * P / solid_angle
        power_w = (
            value * solid_angle_sr
            / (K_M * v_lambda)
        )

    else:
        raise ValueError("Unsupported input unit.")

    # Calculate the other units from radiant power.
    wavelength_m = wavelength_nm * 1e-9
    energy_per_photon = H * C / wavelength_m

    photon_flux_mol_s = power_w / energy_per_photon / NA
    microeinstein_s = photon_flux_mol_s * 1e6
    milliwatts = power_w * 1000.0

    v_lambda = photopic_efficiency(wavelength_nm)

    if solid_angle_sr > 0:
        candela = (
            K_M * v_lambda * power_w / solid_angle_sr
        )
    else:
        candela = None

    return {
        "Microeinstein (µE/s)": microeinstein_s,
        "Watt (W)": power_w,
        "Milliwatt (mW)": milliwatts,
        "Candela (cd)": candela,
    }


# --------------------------------------------------
# User interface
# --------------------------------------------------
st.title("💡 Optical Unit Converter")

st.write(
    "Convert photon flux, optical radiant power, and "
    "luminous intensity for monochromatic light."
)

st.info(
    "Assumptions: monochromatic light, photon flux expressed "
    "in µmol/s, and candela calculated using the photopic "
    "response of the human eye."
)

with st.form("conversion_form"):
    input_unit = st.selectbox(
        "Input unit",
        [
            "Microeinstein (µE/s)",
            "Watt (W)",
            "Milliwatt (mW)",
            "Candela (cd)",
        ],
    )

    value = st.number_input(
        "Measured intensity / value",
        min_value=0.0,
        value=1.0,
        format="%.8g",
    )

    wavelength_nm = st.number_input(
        "Wavelength (nm)",
        min_value=380.0,
        max_value=780.0,
        value=555.0,
        step=1.0,
        help="The current photopic model supports 380–780 nm.",
    )

    solid_angle_sr = st.number_input(
        "Emission solid angle (sr)",
        min_value=0.000001,
        max_value=12.566371,
        value=1.0,
        format="%.6f",
        help=(
            "Required for candela conversions. "
            "A full sphere is approximately 4π sr. "
            "Use the effective emission solid angle."
        ),
    )

    submitted = st.form_submit_button(
        "Convert units",
        type="primary",
        use_container_width=True,
    )

if submitted:
    try:
        results = calculate_conversions(
            value=value,
            input_unit=input_unit,
            wavelength_nm=wavelength_nm,
            solid_angle_sr=solid_angle_sr,
        )

        st.subheader("Conversion results")

        # Display the equivalent in all four units.
        #for unit, result in results.items():
            #if result is None:
                #formatted = "Not available"
            #else:
                #formatted = f"{result:.8g}"

            #st.metric(unit, formatted)

        st.caption(
            f"Wavelength: {wavelength_nm:g} nm | "
            f"Photopic efficiency V(λ): "
            f"{photopic_efficiency(wavelength_nm):.6g} | "
            f"Solid angle: {solid_angle_sr:g} sr"
        )

        
        df = pd.DataFrame({
            "Unit": list(results.keys()),
            "Equivalent value": [
                results[k] for k in results
                ],
            })
            st.dataframe(df, hide_index=True, use_container_width=True)

    except ValueError as error:
        st.error(str(error))

st.divider()
st.caption(
    "Note: candela is a photometric quantity, not a direct "
    "radiometric unit. Results depend on wavelength, the "
    "photopic response model, and the assumed solid angle."
)


