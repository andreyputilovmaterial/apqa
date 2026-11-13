import { defineComponent, h, markRaw, onMounted } from 'vue';


import Window from './window_component';
import safetyUrlCheck from './safetycheck';
import logError from '@/common_components/_log_error_proxy';
import { createModal } from '@/common_components/modals/modals';
import TestPageModal from '@/app/testpage/index';
import ProjectSettingsModal from '@/app/project_settings/index';


const LinksSiteComponent = {
  template: `<span class="apqa-navlinks-manipulate-component"></span>`, // empty is raising warning
  setup() {

    const init = () => {

      const readUrl = linkEl => {
        const urlRaw = linkEl.getAttribute( 'href' );
        const url = new URL( urlRaw, window.location.origin );
        url.searchParams.set( 'embed', '1' );
        // const result = url.pathname + url.search + url.hash;
        // return result;
        return url.toString();
      };

      const createLinkHandler = url => {
        const MyWindowSpecificToThisUrl = defineComponent( {
          setup( _, { attrs } ) {
            try {
              return /* render fn */ () => {
                try {
                  return h( Window, {
                    ...attrs,
                    url,
                  } );
                } catch( e ) {
                  logError( e );
                  throw e;
                }
              }
            } catch( e ) {
              logError( e );
              throw e;
            }
          },
        } )
        return function( event ) {
          event.preventDefault();
          ( async function() {
            await createModal( MyWindowSpecificToThisUrl )
          } )();
          return false;
        }
      }

      const VUE_MODALS = {
        testpage: TestPageModal,
        project: ProjectSettingsModal,
      };

      const createVueModalHandler = ( name ) => function( event ) {
        event.preventDefault();
        const Component = VUE_MODALS[ name ];
        if( !Component ) {
          logError( `Unknown vue modal name: ${name}` );
          return false;
        }
        ( async function() {
          await createModal( Component );
        } )();
        return false;
      };

      Array.from( document.querySelectorAll( '[navigation-role] a, a[navigation-role]' ) ).forEach( function( linkEl ) {
        try {

          const vueModalName = linkEl.getAttribute( 'data-open-vue-modal' );
          if( vueModalName ) {
            linkEl.addEventListener( 'click', createVueModalHandler( vueModalName ) );
            return;
          }

          const url = readUrl( linkEl );
          if( safetyUrlCheck( url ) )
            linkEl.addEventListener( 'click', createLinkHandler( url ) );

        } catch( e ) {
          try {
            logError( e );
          } catch( ee ) {
            // ok to ignore
          }
        }
      } );
    };


    onMounted( async () => {
      await Promise.all( [
        ( function() {
          init();
          return null;
        } )(),
      ] )
    } );

  },
}
export default LinksSiteComponent;
